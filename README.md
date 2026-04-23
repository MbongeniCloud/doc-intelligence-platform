#  AI-Powered Document Intelligence & Compliance Platform

> An enterprise-grade document processing system built on Microsoft Azure — automating the extraction, classification, risk assessment, and POPIA-compliant handling of sensitive financial documents using AI.

<br>

![CI](https://github.com/MbongeniCloud/doc-intelligence-platform/actions/workflows/ci.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Azure](https://img.shields.io/badge/cloud-Microsoft%20Azure-0078D4?logo=microsoft-azure&logoColor=white)
![Region](https://img.shields.io/badge/region-South%20Africa%20North-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

##  Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Real-World Scenarios](#-real-world-scenarios)
- [Architecture](#-architecture)
- [Azure Services](#-azure-services)
- [Security & Compliance Design](#-security--compliance-design)
- [PII Scrubbing Layer](#-pii-scrubbing-layer)
- [Sample AI Output](#-sample-ai-output)
- [Project Structure](#-project-structure)
- [Technical Challenges](#-technical-challenges)
- [Local Setup](#-local-setup)
- [Deploy to Azure](#-deploy-to-azure)
- [Test Results](#-test-results)
- [What I Learned](#-what-i-learned)

---

##  The Problem

South African financial institutions process **thousands of documents every day**:

- KYC onboarding — IDs, proof of address, bank statements
- Loan applications — payslips, credit history, tax returns
- Compliance reviews — contracts, regulatory filings, FICA documents

**The current reality at most institutions:**

| Step | Manual Process | Time |
|------|---------------|------|
| Employee reads document | Manual | 5–15 min |
| Types data into system | Manual | 5–10 min |
| Checks compliance | Manual | 10–20 min |
| Flags suspicious docs | Manual (if at all) | Variable |
| **Total per document** | **Human-dependent** | **20–45 min** |

This is slow, expensive, inconsistent — and a **POPIA liability** every time a document passes through human hands without proper data governance.

---

##  The Solution

Upload a document. Get a structured, AI-generated intelligence report in **under 30 seconds**.

The platform automatically:

- **Extracts** all text, tables, and key-value pairs using Azure Document Intelligence
- **Scrubs PII** before any data touches the LLM (privacy-by-design)
- **Classifies** the document type using GPT-4o
- **Detects sensitive data** and flags POPIA compliance risks
- **Assesses fraud signals** — inconsistencies, formatting anomalies, suspicious values
- **Summarises financial health** for loan/credit applications
- **Stores results securely** with full audit trail

**Business impact:**
- 90%+ reduction in manual document processing time
- Consistent, auditable compliance checks on every document
- Fraud detection that scales without additional headcount
- Data never leaves South Africa (POPIA §72 data residency)

---

##  Real-World Scenarios

### Scenario 1 — KYC / Account Opening

**Context:** A customer uploads their ID and bank statement to open an account.

**Without this system:** Employee manually verifies identity, extracts details, checks for suspicious info.

**With this system:**
```
Document uploaded → Pipeline triggers automatically

Extracted:  Name: John Smith | ID: [REDACTED] | Account: [REDACTED]
Classified: bank_statement (confidence: 0.95)
PII found:  SA ID number, bank account number, salary info
Risk:       MEDIUM — document contains sensitive personal data
Fraud:      None detected
POPIA recs: Encrypt at rest | Restrict to authorised roles | SA-region storage
```

Result: Processed in 28 seconds. Full audit trail. No human saw raw PII.

---

### Scenario 2 — Loan Application Processing

**Context:** Applicant submits payslip and 3 months of bank statements.

**AI Output:**
```json
{
  "category": "bank_statement",
  "financial_summary": {
    "income": "R35,000/month",
    "expenses": "R21,500/month",
    "balance": "R12,500",
    "debt_ratio": "61%",
    "assessment": "Stable income. Debt ratio elevated — medium credit risk."
  },
  "key_insights": [
    "Consistent salary from single employer for 6+ months",
    "Monthly rent R8,500 — 24% of income",
    "No irregular large withdrawals detected"
  ],
  "risk_level": "medium"
}
```

Credit officer gets a structured report instead of reading 90 pages manually.

---

### Scenario 3 — POPIA Compliance Audit

**Context:** Legal team needs to verify all stored documents have been properly classified for data sensitivity.

**The system scans every document and returns:**
- Exact PII types present
- Risk level (low / medium / high / critical)
- Specific remediation actions required
- Whether document meets POPIA storage requirements

---

### Scenario 4 — Fraud Detection

**Context:** A loan applicant submits what appears to be a bank statement.

**AI flags:**
```json
{
  "fraud_signals": [
    "Balance figures inconsistent with transaction history",
    "Document formatting deviates from standard FNB template",
    "Employer name not verifiable against known SA company registry patterns"
  ],
  "risk_level": "critical",
  "confidence": 0.31
}
```

Low confidence + multiple fraud signals = flagged for manual review before any decision is made.

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client / Staff Portal                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Upload PDF / Image
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│               Azure Blob Storage — uploads/ container               │
│              Private | TLS 1.2+ | No public access                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Blob trigger (event-driven)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Azure Functions (Python 3.11 | Consumption)            │
│                                                                     │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  PII Scrubber   │───▶│ Doc Intelligence │───▶│  GPT-4o       │  │
│  │  Redact before  │    │ Extract text,    │    │  Classify     │  │
│  │  LLM sees data  │    │ tables, KV pairs │    │  Summarise    │  │
│  └─────────────────┘    └──────────────────┘    │  Risk + Fraud │  │
│                                                  └───────────────┘  │
└──────────────┬──────────────────────────────┬───────────────────────┘
               │                              │
    ┌──────────▼──────────┐      ┌────────────▼────────────┐
    │    Blob Storage      │      │    Application Insights  │
    │  processed/ results/ │      │  Telemetry | Alerts      │
    └─────────────────────┘      └─────────────────────────┘
               │
    ┌──────────▼──────────┐
    │    Azure Key Vault   │
    │  All secrets stored  │
    │  Managed Identity    │
    └─────────────────────┘
```

### Processing Flow

```
1. Document lands in uploads/ container
         ↓
2. Azure Function fires automatically (blob trigger)
         ↓
3. PII Scrubber redacts SA IDs, account numbers, phones, emails
         ↓
4. Azure Document Intelligence extracts text, tables, key-value pairs
         ↓
5. GPT-4o receives SCRUBBED text — classifies, summarises, assesses risk
         ↓
6. Result JSON stored in results/ container
         ↓
7. Original document moved to processed/ container
         ↓
8. High-risk documents trigger alerts via Application Insights
```

---

##  Azure Services

| Service | Purpose | Why This Choice |
|---------|---------|-----------------|
| **Azure Blob Storage** | Document ingestion + result storage | Private containers, server-side encryption, lifecycle management |
| **Azure Functions** | Event-driven processing pipeline | Scales to zero cost, triggers on blob upload automatically |
| **Azure AI Document Intelligence** | Extract text, tables, key-value pairs | Purpose-built for documents — far more accurate than raw OCR |
| **Azure OpenAI (GPT-4o)** | Classify, summarise, detect risk | Best-in-class reasoning, JSON output mode, SA North region available |
| **Azure Key Vault** | Secrets management | Zero hardcoded credentials — managed identity access only |
| **Microsoft Defender for Cloud** | Threat protection on storage | Detects anomalous access patterns, malware in uploads |
| **Application Insights** | Telemetry, logging, alerting | Full observability — every document tracked end-to-end |
| **Azure RBAC** | Access control | Role assignments, not connection strings |
| **Bicep (IaC)** | Infrastructure as code | Entire environment recreatable in one command |

---

##  Security & Compliance Design

Security was a **first-class design concern**, not an afterthought.

| Control | Implementation | Why It Matters |
|---------|---------------|----------------|
| No public blob access | `allowBlobPublicAccess: false` in Bicep | Documents never accidentally exposed |
| Zero hardcoded secrets | All keys in Key Vault | No credentials in code, logs, or git history |
| Managed identity | System-assigned identity on Function App | No service principal passwords to rotate or leak |
| RBAC | Fine-grained role assignments | Least-privilege — Function only reads secrets it needs |
| TLS 1.2+ enforced | `minimumTlsVersion: TLS1_2` | Encryption in transit |
| Soft delete + purge protection | Key Vault 7-day retention | Recoverable from accidental deletion |
| PII scrubbing | Before text reaches LLM | Personal data never sent to external model |
| Data residency | South Africa North region | POPIA §72 — personal data stays in SA |
| Audit trail | Every document logged with timestamp | Compliance evidence on demand |

### POPIA Compliance

South Africa's Protection of Personal Information Act (POPIA, 2021) governs how organisations collect, store, and process personal data. This platform was designed to comply:

- **Section 19** — Appropriate security measures on personal information 
- **Section 72** — Personal information must not be transferred outside SA without adequate protection 
- **Section 22** — Notification of security compromises (Defender for Cloud alerts) 
- Automated PII detection on every document processed 
- Audit trail of every access and processing event 

---

##  PII Scrubbing Layer

A dedicated scrubbing layer was added based on real enterprise feedback: **the LLM should never see raw personal data**.

Before document text reaches GPT-4o, the `PIIScrubber` replaces sensitive values with typed tokens:

```
Input:  "ID Number: 9001015009087, Account: 62012345678, Email: john@fnb.co.za"
Output: "ID Number: [SA_ID_01], Account: [ACCOUNT_NUM_02], Email: [EMAIL_03]"
```

The redaction map (`{token: original_value}`) is kept server-side only — GPT-4o receives structure without substance.

**Patterns covered:**
- SA ID numbers (13-digit)
- Bank account numbers (8–11 digits)
- South African phone numbers (+27 / 0xx format)
- Email addresses
- Sensitive key-value pairs (id number, account number, address, phone, email)

---

##  Sample AI Output

Real output from the pipeline on a test bank statement:

```json
{
  "source_document": "uploads/2026/04/22/bank_statement_jan.pdf",
  "environment": "dev",
  "duration_seconds": 27.4,
  "extraction": {
    "pages": 1,
    "language": "en",
    "char_count": 135,
    "key_value_pairs": {
      "Account Holder": "John Smith",
      "Salary": "R35000.00",
      "Balance": "R12500.00"
    }
  },
  "analysis": {
    "category": "bank_statement",
    "summary": "FNB bank statement for John Smith detailing January 2024 transactions. Shows stable salary income of R35,000 with controlled monthly expenses.",
    "risk_level": "medium",
    "risk_factors": ["Document contains high-sensitivity personal financial data"],
    "fraud_signals": [],
    "key_insights": [
      "Account holder: John Smith",
      "Monthly income: R35,000",
      "Account balance: R12,500",
      "No irregular transactions detected",
      "Single income source identified"
    ],
    "financial_summary": {
      "income": "R35,000",
      "balance": "R12,500",
      "assessment": "Stable income with controlled expenses. Suitable for credit assessment."
    },
    "confidence": 0.95
  },
  "pii_scan": {
    "has_pii": true,
    "pii_types": ["SA ID number", "bank account number", "salary info"],
    "risk_level": "high",
    "recommendations": [
      "Encrypt document at rest using Azure Storage Service Encryption",
      "Restrict access to authorised personnel only via RBAC",
      "Ensure data is stored in SA-region data centre (POPIA §72)"
    ]
  }
}
```

---

##  Project Structure

```
doc-intelligence-platform/
│
├── infra/
│   ├── main.bicep                  # All Azure resources as code
│   └── parameters.dev.json         # Environment-specific config
│
├── src/
│   ├── extractors/
│   │   └── document_extractor.py   # Azure Document Intelligence wrapper
│   ├── analyzers/
│   │   ├── document_analyzer.py    # GPT-4o analysis — classify, summarise, risk
│   │   └── pii_scrubber.py         # PII redaction before LLM (POPIA layer)
│   └── storage/
│       └── storage_manager.py      # Blob operations + SAS URL generation
│
├── functions/
│   ├── host.json                   # Azure Functions runtime config
│   ├── requirements.txt            # Function-specific dependencies
│   └── process_document/
│       └── __init__.py             # Blob-triggered pipeline — wires everything together
│
├── tests/
│   ├── test_units.py               # 15 unit tests (fully mocked — no Azure needed)
│   ├── test_scrubber.py            # 6 PII scrubber tests
│   ├── test_analyzer.py            # Live integration test (requires Azure)
│   ├── test_extraction.py          # Live extraction test (requires Azure)
│   └── test_pipeline.py            # Full end-to-end pipeline test
│
├── .github/workflows/
│   └── ci.yml                      # GitHub Actions — test on every push
│
├── .env.example                    # Environment variable template
├── requirements.txt                # Python dependencies
└── README.md
```

---

##  Technical Challenges

Building this taught me things no tutorial covers.

### 1. Model availability differs by region
GPT-4o `2024-08-06` was deprecated in South Africa North by the time I deployed. I had to query available models dynamically and select the correct version (`2024-11-20` with `GlobalStandard` SKU). In production systems, regional model availability is something you have to actively manage.

### 2. Azure Document Intelligence SDK breaking changes
The `begin_analyze_document()` method changed its parameter name from `analyze_request` to `body` in a recent SDK version. No deprecation warning — just a runtime error. Taught me to always pin SDK versions in `requirements.txt` and test after upgrades.

### 3. RBAC propagation delay
After assigning Key Vault roles via the Azure CLI, the permissions take 30–60 seconds to propagate. Immediate secret access attempts return `403 Forbidden`. Had to add explicit sleep in the deployment script — something that bites everyone the first time.

### 4. PowerShell execution policy
Windows blocks npm scripts by default (`PSSecurityException`). Required `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` before any npm-based tooling would run. A real environment setup concern for Windows-based dev teams.

### 5. PII scrubbing before LLM
Initial design sent raw document text directly to GPT-4o. Feedback from a senior engineer correctly identified this as an architectural risk — the LLM should never see actual SA ID numbers or account numbers. Redesigned to include a regex-based scrubbing layer that tokenises sensitive values before inference. This is a real enterprise pattern used in production financial systems.

---

##  Local Setup

**Prerequisites:** Python 3.11+, Azure CLI, Git

```bash
# Clone
git clone https://github.com/MbongeniCloud/doc-intelligence-platform
cd doc-intelligence-platform

# Virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate        # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env             # Windows
# cp .env.example .env             # macOS/Linux
# Edit .env with your Azure service keys

# Run unit tests (no Azure needed)
python -m pytest tests/test_units.py tests/test_scrubber.py -v

# Run full integration tests (requires Azure)
python tests/test_pipeline.py
```

---

##  Deploy to Azure

One-command infrastructure deployment:

```bash
# Login
az login

# Create resource group
az group create --name dociq-rg-dev --location southafricanorth

# Deploy all infrastructure
az deployment group create \
  --resource-group dociq-rg-dev \
  --template-file infra/main.bicep \
  --parameters infra/parameters.dev.json

# Store secrets in Key Vault
az keyvault secret set --vault-name <your-kv-name> \
  --name "document-intelligence-key" --value "<key>"

# Deploy Function App
cd functions
func azure functionapp publish <your-function-app-name> --python
```

**To test:** Upload any PDF to the `uploads` blob container. Check the `results` container ~30 seconds later.

---

##  Test Results

```
================================================
18 passed in 44.00s
================================================

tests/test_units.py::TestDocumentAnalyzer::test_classifies_bank_statement     PASSED
tests/test_units.py::TestDocumentAnalyzer::test_detects_pii                   PASSED
tests/test_units.py::TestDocumentAnalyzer::test_flags_fraud_signals            PASSED
tests/test_units.py::TestDocumentAnalyzer::test_handles_invalid_json_safely   PASSED
tests/test_units.py::TestDocumentAnalyzer::test_no_fraud_on_clean_document    PASSED
tests/test_units.py::TestDocumentAnalyzer::test_financial_summary_extracted   PASSED
tests/test_units.py::TestExtractedDocument::test_stores_all_fields            PASSED
tests/test_units.py::TestExtractedDocument::test_defaults_to_empty_collections PASSED
tests/test_units.py::TestExtractedDocument::test_metadata_stored_correctly    PASSED
tests/test_units.py::TestPipelineLogic::test_hint_document_type_bank          PASSED
tests/test_units.py::TestPipelineLogic::test_hint_document_type_id            PASSED
tests/test_units.py::TestPipelineLogic::test_hint_document_type_default       PASSED
tests/test_units.py::TestPipelineLogic::test_detect_content_type_pdf          PASSED
tests/test_units.py::TestPipelineLogic::test_detect_content_type_jpg          PASSED
tests/test_units.py::TestPipelineLogic::test_detect_content_type_unknown      PASSED
tests/test_scrubber.py::test_scrubs_sa_id_number                              PASSED
tests/test_scrubber.py::test_scrubs_email                                     PASSED
tests/test_scrubber.py::test_scrubs_phone                                     PASSED
tests/test_scrubber.py::test_scrubs_sensitive_kv_pairs                        PASSED
tests/test_scrubber.py::test_clean_text_unchanged                             PASSED
tests/test_scrubber.py::test_redaction_map_contains_originals                 PASSED

Unit tests run without Azure credentials — all external services mocked.
Integration tests available separately (require live Azure resources).
```

---

##  What I Learned

This project went well beyond "follow a tutorial." Real challenges that came up:

**Cloud architecture:** Designing systems where components are loosely coupled, event-driven, and independently scalable. Understanding why managed identity beats connection strings, and why IaC matters when you need to tear down and rebuild.

**Enterprise AI patterns:** LLMs are powerful but naive — they need guardrails. PII scrubbing before inference, structured JSON output mode, temperature tuning for consistency, and graceful degradation when the model returns unexpected output.

**Security thinking:** Every design decision has a security implication. Public vs private containers, secret rotation, RBAC scope, audit logging. These aren't add-ons — they're requirements from day one in a regulated environment.

**South African compliance context:** POPIA isn't just a checkbox. It affects architecture decisions — data residency, access controls, breach notification, and how you handle PII throughout the entire data lifecycle.

**Debugging distributed systems:** When something fails in a cloud pipeline, the error could be in the SDK version, the region, the RBAC propagation delay, or the model deprecation schedule. Systematic debugging across multiple services is a real skill.

---

##  Tech Stack

`Python 3.11` · `Azure Functions` · `Azure Blob Storage` · `Azure AI Document Intelligence` · `Azure OpenAI GPT-4o` · `Azure Key Vault` · `Microsoft Defender for Cloud` · `Application Insights` · `Bicep (IaC)` · `GitHub Actions` · `pytest` · `Regex (PII scrubbing)`

---

##  License

MIT — free to use, adapt, and build on.

---

*Built as a portfolio project demonstrating enterprise-grade cloud and AI engineering with real Azure infrastructure, security-first design, and South African compliance context.*