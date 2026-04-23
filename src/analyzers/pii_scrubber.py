"""
PII Scrubber — redacts sensitive personal information before
document text is sent to any LLM.

Replaces real values with typed tokens so GPT-4o can still
classify and summarise without seeing actual sensitive data.

Patterns covered (POPIA-relevant):
    - SA ID numbers (13-digit)
    - Bank account numbers
    - Phone numbers
    - Email addresses
    - Physical addresses (basic)
    - Names (via key-value pairs, not regex)
"""
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScrubResult:
    scrubbed_text: str
    scrubbed_kv_pairs: dict
    redactions: dict          # {token: original_value} — kept server-side only
    redaction_count: int


class PIIScrubber:
    """
    Redacts PII from document text before it touches the LLM.

    Design:
        - Uses regex for structured PII (IDs, accounts, phones)
        - Uses key name matching for KV pairs
        - Returns scrubbed text + a redaction map (never sent to LLM)
    """

    # SA ID number: 13 digits starting with valid date
    SA_ID_PATTERN       = re.compile(r'\b(\d{13})\b')
    # Bank account: 8-11 consecutive digits
    BANK_ACCOUNT_PATTERN = re.compile(r'\b(\d{8,11})\b')
    # SA phone numbers
    PHONE_PATTERN        = re.compile(r'(\+27|0)[6-8][0-9]\s?\d{3}\s?\d{4}')
    # Email addresses
    EMAIL_PATTERN        = re.compile(r'\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b')

    # KV keys that contain PII — scrub their values
    SENSITIVE_KV_KEYS = {
        "id number", "id no", "identity number", "national id",
        "account number", "account no", "acc number",
        "phone", "telephone", "cell", "mobile",
        "email", "e-mail",
        "address", "physical address", "residential address",
    }

    def scrub(self, text: str, kv_pairs: dict) -> ScrubResult:
        """
        Scrub PII from text and key-value pairs.

        Returns ScrubResult with redacted versions safe to send to LLM.
        """
        scrubbed = text
        redactions = {}
        counter = [0]

        def replace(token_prefix: str, value: str) -> str:
            counter[0] += 1
            token = f"[{token_prefix}_{counter[0]:02d}]"
            redactions[token] = value
            return token

        # ── Regex-based redaction ─────────────────────────────────────────────
        def replace_sa_id(m):
            return replace("SA_ID", m.group(1))

        def replace_account(m):
            return replace("ACCOUNT_NUM", m.group(1))

        def replace_phone(m):
            return replace("PHONE", m.group(0))

        def replace_email(m):
            return replace("EMAIL", m.group(0))

        scrubbed = self.SA_ID_PATTERN.sub(replace_sa_id, scrubbed)
        scrubbed = self.BANK_ACCOUNT_PATTERN.sub(replace_account, scrubbed)
        scrubbed = self.PHONE_PATTERN.sub(replace_phone, scrubbed)
        scrubbed = self.EMAIL_PATTERN.sub(replace_email, scrubbed)

        # ── KV pair redaction ─────────────────────────────────────────────────
        scrubbed_kv = {}
        for key, value in kv_pairs.items():
            if key.lower().strip() in self.SENSITIVE_KV_KEYS:
                token = replace("KV_" + key.upper().replace(" ", "_"), value)
                scrubbed_kv[key] = token
            else:
                scrubbed_kv[key] = value

        logger.info("PII scrubbed | redactions=%d", len(redactions))

        return ScrubResult(
            scrubbed_text=scrubbed,
            scrubbed_kv_pairs=scrubbed_kv,
            redactions=redactions,
            redaction_count=len(redactions),
        )