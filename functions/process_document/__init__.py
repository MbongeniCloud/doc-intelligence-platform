"""
Azure Function: process_document
Trigger: Blob Storage — fires on every file uploaded to 'uploads' container.

Pipeline:
    1. Read document bytes from blob
    2. Extract text via Azure Document Intelligence
    3. Analyse with GPT-4o (classify, PII scan, risk assessment)
    4. Store JSON result in 'results' container
    5. Move document to 'processed' container
"""
import json
import logging
import os
import sys
import time

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.extractors.document_extractor import DocumentExtractor
from src.analyzers.document_analyzer import DocumentAnalyzer

logger = logging.getLogger(__name__)

# ── Config from environment ───────────────────────────────────────────────────
STORAGE_ACCOUNT_NAME  = os.environ["STORAGE_ACCOUNT_NAME"]
STORAGE_ACCOUNT_KEY   = os.environ["STORAGE_ACCOUNT_KEY"]
DOC_AI_ENDPOINT       = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
DOC_AI_KEY            = os.environ["DOCUMENT_INTELLIGENCE_KEY"]
OPENAI_ENDPOINT       = os.environ["AZURE_OPENAI_ENDPOINT"]
OPENAI_KEY            = os.environ["AZURE_OPENAI_KEY"]
OPENAI_DEPLOYMENT     = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
ENVIRONMENT           = os.environ.get("ENVIRONMENT", "dev")

# ── Lazy-loaded clients (reused across warm invocations) ─────────────────────
_extractor = None
_analyzer  = None
_blob_client = None


def get_clients():
    global _extractor, _analyzer, _blob_client

    if _extractor is None:
        _extractor = DocumentExtractor(
            endpoint=DOC_AI_ENDPOINT,
            api_key=DOC_AI_KEY,
        )

    if _analyzer is None:
        _analyzer = DocumentAnalyzer(
            endpoint=OPENAI_ENDPOINT,
            api_key=OPENAI_KEY,
            deployment=OPENAI_DEPLOYMENT,
        )

    if _blob_client is None:
        conn_str = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={STORAGE_ACCOUNT_NAME};"
            f"AccountKey={STORAGE_ACCOUNT_KEY};"
            f"EndpointSuffix=core.windows.net"
        )
        _blob_client = BlobServiceClient.from_connection_string(conn_str)

    return _extractor, _analyzer, _blob_client


def detect_content_type(blob_name: str) -> str:
    ext = blob_name.rsplit(".", 1)[-1].lower() if "." in blob_name else ""
    return {
        "pdf":  "application/pdf",
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
        "png":  "image/png",
    }.get(ext, "application/pdf")


def hint_document_type(blob_name: str) -> str:
    name = blob_name.lower()
    if any(x in name for x in ["id_doc", "passport", "national_id"]): return "id"
    if any(x in name for x in ["statement", "bank"]):                  return "bank_statement"
    if any(x in name for x in ["payslip", "salary"]):                  return "general"
    if any(x in name for x in ["contract", "agreement"]):              return "contract"
    return "general"


# ── Main Function ─────────────────────────────────────────────────────────────
app = func.FunctionApp()


@app.blob_trigger(
    arg_name="myblob",
    path="uploads/{name}",
    connection="AzureWebJobsStorage",
)
def process_document(myblob: func.InputStream) -> None:
    blob_name = myblob.name
    start     = time.time()

    logger.info("=== Pipeline started | blob=%s | size=%d ===", blob_name, myblob.length)

    try:
        extractor, analyzer, blob_svc = get_clients()

        # ── Step 1: Read bytes ────────────────────────────────────────────────
        document_bytes = myblob.read()
        content_type   = detect_content_type(blob_name)
        doc_type_hint  = hint_document_type(blob_name)

        # ── Step 2: Extract ───────────────────────────────────────────────────
        logger.info("Step 2: Extracting | model=prebuilt-layout")
        extracted = extractor.extract_from_bytes(document_bytes, content_type, doc_type_hint)
        logger.info("Extracted | chars=%d | kv_pairs=%d", len(extracted.raw_text), len(extracted.key_value_pairs))

        # ── Step 3: Analyse ───────────────────────────────────────────────────
        logger.info("Step 3: Analysing with GPT-4o")
        analysis = analyzer.analyze(extracted.raw_text, extracted.key_value_pairs, doc_type_hint)
        logger.info("Analysed | category=%s | risk=%s | pii=%s",
                    analysis.category, analysis.risk_level, analysis.pii_scan.has_pii)

        # ── Step 4: Store result ──────────────────────────────────────────────
        logger.info("Step 4: Storing result")
        result_name = blob_name.rsplit(".", 1)[0] + "_result.json"
        result_payload = {
            "source_document": blob_name,
            "environment": ENVIRONMENT,
            "duration_seconds": round(time.time() - start, 2),
            "extraction": {
                "pages": extracted.pages,
                "language": extracted.language,
                "char_count": len(extracted.raw_text),
                "key_value_pairs": extracted.key_value_pairs,
            },
            "analysis": {
                "category": analysis.category,
                "summary": analysis.summary,
                "risk_level": analysis.risk_level,
                "risk_factors": analysis.risk_factors,
                "fraud_signals": analysis.fraud_signals,
                "key_insights": analysis.key_insights,
                "financial_summary": analysis.financial_summary,
                "confidence": analysis.confidence,
            },
            "pii_scan": {
                "has_pii": analysis.pii_scan.has_pii,
                "pii_types": analysis.pii_scan.pii_types,
                "risk_level": analysis.pii_scan.risk_level,
                "recommendations": analysis.pii_scan.recommendations,
            },
        }

        results_client = blob_svc.get_blob_client(container="results", blob=result_name)
        results_client.upload_blob(
            json.dumps(result_payload, indent=2).encode("utf-8"),
            overwrite=True,
        )
        logger.info("Result stored | blob=results/%s", result_name)

        # ── Step 5: Move to processed ─────────────────────────────────────────
        logger.info("Step 5: Moving to processed container")
        source_url = (
            f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/uploads/{blob_name.split('uploads/')[-1]}"
        )
        dest = blob_svc.get_blob_client(container="processed", blob=blob_name.split("uploads/")[-1])
        dest.start_copy_from_url(source_url)

        src = blob_svc.get_blob_client(container="uploads", blob=blob_name.split("uploads/")[-1])
        src.delete_blob()

        duration = round(time.time() - start, 2)
        logger.info("=== Pipeline complete | duration=%ss | result=results/%s ===", duration, result_name)

        # ── Alert on high risk ────────────────────────────────────────────────
        if analysis.risk_level in ("high", "critical"):
            logger.warning("HIGH RISK DOCUMENT DETECTED | blob=%s | risk=%s | factors=%s",
                           blob_name, analysis.risk_level, analysis.risk_factors)

    except Exception as e:
        logger.exception("Pipeline FAILED | blob=%s | error=%s", blob_name, e)
        raise