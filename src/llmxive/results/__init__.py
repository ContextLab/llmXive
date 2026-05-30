"""results package — execution receipts (spec 016).

Re-exports land here as the sub-modules are implemented.
"""

from __future__ import annotations

from llmxive.results.harness import mint_receipt, result_backed  # T026
from llmxive.results.receipt import (  # T024
    Receipt,
    load_signing_key,
    sign_receipt,
    verify_receipt,
)

__all__ = [
    "Receipt",
    "load_signing_key",
    "mint_receipt",
    "result_backed",
    "sign_receipt",
    "verify_receipt",
]
