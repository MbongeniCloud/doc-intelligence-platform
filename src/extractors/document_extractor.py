"""
Document extractor using Azure AI Document Intelligence.
"""
import logging
from dataclasses import dataclass, field
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    raw_text: str
    key_value_pairs: dict
    tables: list
    document_type: str
    confidence_score: float
    pages: int
    language: str
    entities: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class DocumentExtractor:
    PREBUILT_MODELS = {
        "general":        "prebuilt-layout",
        "id":             "prebuilt-layout",
        "invoice":        "prebuilt-layout",
        "bank_statement": "prebuilt-layout",
        "contract":       "prebuilt-layout",
    }

    def __init__(self, endpoint: str, api_key: str):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        logger.info("DocumentExtractor ready | endpoint=%s", endpoint)

    def extract_from_bytes(self, document_bytes: bytes, content_type: str, document_type: str = "general") -> ExtractedDocument:
        model_id = self.PREBUILT_MODELS.get(document_type, "prebuilt-layout")
        logger.info("Extracting | model=%s | size=%d bytes", model_id, len(document_bytes))

        poller = self.client.begin_analyze_document(
            model_id=model_id,
            body=document_bytes,
            content_type=content_type,
        )
        result = poller.result()
        return self._parse_result(result, document_type)

    def _parse_result(self, result, document_type: str) -> ExtractedDocument:
        raw_text = result.content or ""

        kv_pairs = {}
        if result.key_value_pairs:
            for kv in result.key_value_pairs:
                if kv.key and kv.value and (kv.confidence or 0) > 0.5:
                    kv_pairs[kv.key.content.strip()] = kv.value.content.strip()

        tables = []
        if result.tables:
            for table in result.tables:
                grid = {}
                for cell in table.cells:
                    if cell.row_index not in grid:
                        grid[cell.row_index] = {}
                    grid[cell.row_index][cell.column_index] = cell.content
                tables.append(grid)

        language = "en"
        if result.languages:
            language = max(result.languages, key=lambda l: l.confidence).locale

        confidence = 0.0
        if result.documents:
            confidence = result.documents[0].confidence or 0.0

        pages = len(result.pages) if result.pages else 1

        logger.info("Done | pages=%d | kv=%d | tables=%d | confidence=%.2f",
                    pages, len(kv_pairs), len(tables), confidence)

        return ExtractedDocument(
            raw_text=raw_text,
            key_value_pairs=kv_pairs,
            tables=tables,
            document_type=document_type,
            confidence_score=confidence,
            pages=pages,
            language=language,
            metadata={"char_count": len(raw_text)},
        )