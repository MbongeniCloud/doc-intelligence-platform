"""
End-to-end pipeline test — simulates what the Azure Function does,
but runs locally without needing the Function runtime.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.extractors.document_extractor import DocumentExtractor
from src.analyzers.document_analyzer import DocumentAnalyzer

SAMPLE_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>stream
BT /F1 14 Tf 50 750 Td
(FNB Bank Statement) Tj 0 -30 Td
(Account Holder: John Smith) Tj 0 -25 Td
(ID Number: 9001015009087) Tj 0 -25 Td
(Account Number: 62012345678) Tj 0 -25 Td
(Salary: R35000.00) Tj 0 -25 Td
(Balance: R12500.00) Tj
ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000528 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
607
%%EOF"""


def test_full_pipeline():
    print("\n" + "="*55)
    print("  FULL PIPELINE TEST — Extract → Analyse → Result")
    print("="*55)

    # Step 1: Extract
    print("\n[1/3] Extracting document...")
    extractor = DocumentExtractor(
        endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"],
        api_key=os.environ["DOCUMENT_INTELLIGENCE_KEY"],
    )
    extracted = extractor.extract_from_bytes(SAMPLE_PDF, "application/pdf", "bank_statement")
    print(f"      ✅ Pages: {extracted.pages} | Chars: {len(extracted.raw_text)}")
    print(f"      ✅ Text: {extracted.raw_text[:80]}...")

    # Step 2: Analyse
    print("\n[2/3] Analysing with GPT-4o...")
    analyzer = DocumentAnalyzer(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    )
    analysis = analyzer.analyze(extracted.raw_text, extracted.key_value_pairs, "bank_statement")
    print(f"      ✅ Category:  {analysis.category}")
    print(f"      ✅ Risk:      {analysis.risk_level}")
    print(f"      ✅ PII found: {analysis.pii_scan.pii_types}")
    print(f"      ✅ Fraud:     {analysis.fraud_signals or 'None'}")

    # Step 3: Build result payload
    print("\n[3/3] Building result payload...")
    result = {
        "extraction": {
            "pages": extracted.pages,
            "char_count": len(extracted.raw_text),
            "key_value_pairs": extracted.key_value_pairs,
        },
        "analysis": {
            "category": analysis.category,
            "summary": analysis.summary,
            "risk_level": analysis.risk_level,
            "key_insights": analysis.key_insights,
            "fraud_signals": analysis.fraud_signals,
            "financial_summary": analysis.financial_summary,
        },
        "pii_scan": {
            "has_pii": analysis.pii_scan.has_pii,
            "pii_types": analysis.pii_scan.pii_types,
            "recommendations": analysis.pii_scan.recommendations,
        },
    }
    print(f"      ✅ Result payload built ({len(json.dumps(result))} bytes)")

    print("\n" + "="*55)
    print("  SUMMARY")
    print("="*55)
    print(f"  Document:   {analysis.category}")
    print(f"  Summary:    {analysis.summary[:80]}...")
    print(f"  Risk:       {analysis.risk_level.upper()}")
    print(f"  PII:        {', '.join(analysis.pii_scan.pii_types)}")
    print(f"  Insights:   {len(analysis.key_insights)} found")
    print("="*55)
    print("\n✅ FULL PIPELINE TEST PASSED\n")


if __name__ == "__main__":
    test_full_pipeline()