"""
Live test — sends a real document to Azure Document Intelligence.
Run with: python tests/test_extraction.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.extractors.document_extractor import DocumentExtractor

def test_with_sample_text_pdf():
    endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
    api_key  = os.environ["DOCUMENT_INTELLIGENCE_KEY"]

    extractor = DocumentExtractor(endpoint=endpoint, api_key=api_key)

    # Create a minimal test PDF in memory (no file needed)
    sample_pdf = b"""%PDF-1.4
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

    print("\n=== Sending test document to Azure Document Intelligence ===\n")
    result = extractor.extract_from_bytes(sample_pdf, "application/pdf", "bank_statement")

    print(f"✅ Pages:      {result.pages}")
    print(f"✅ Language:   {result.language}")
    print(f"✅ Characters: {len(result.raw_text)}")
    print(f"✅ Confidence: {result.confidence_score:.2f}")
    print(f"\n--- Extracted Text ---")
    print(result.raw_text[:500])
    print(f"\n--- Key-Value Pairs ---")
    for k, v in result.key_value_pairs.items():
        print(f"  {k}: {v}")

    assert result.raw_text != "", "Should have extracted text"
    print("\n✅ TEST PASSED — Azure Document Intelligence is working!")

if __name__ == "__main__":
    test_with_sample_text_pdf()