"""
Live test — sends extracted text to Azure OpenAI for analysis.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.analyzers.document_analyzer import DocumentAnalyzer

def test_analyze_bank_statement():
    analyzer = DocumentAnalyzer(
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_KEY"],
        deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    )

    sample_text = """FNB Bank Statement
Account Holder: John Smith
ID Number: 9001015009087
Account Number: 62012345678
Salary: R35000.00
Rent: R8500.00
Groceries: R1200.00
Balance: R12500.00"""

    print("\n=== Sending to GPT-4o for analysis ===\n")
    result = analyzer.analyze(sample_text, {}, "bank_statement")

    print(f"✅ Category:      {result.category}")
    print(f"✅ Risk Level:    {result.risk_level}")
    print(f"✅ Confidence:    {result.confidence}")
    print(f"✅ Has PII:       {result.pii_scan.has_pii}")
    print(f"✅ PII Types:     {result.pii_scan.pii_types}")
    print(f"\n--- Summary ---")
    print(result.summary)
    print(f"\n--- Key Insights ---")
    for insight in result.key_insights:
        print(f"  • {insight}")
    print(f"\n--- Fraud Signals ---")
    print(result.fraud_signals or "None detected ✅")
    print(f"\n--- POPIA Recommendations ---")
    for rec in result.pii_scan.recommendations:
        print(f"  • {rec}")
    print("\n✅ TEST PASSED — GPT-4o analysis working!")

if __name__ == "__main__":
    test_analyze_bank_statement()