"""claims package — claim-verification layer (spec 016).

Re-exports land here as the sub-modules are implemented.
"""

from __future__ import annotations

from llmxive.claims.service import process_document   # T017
from llmxive.claims.gate import CLAIM_MARKER_PREFIX   # T010

__all__: list[str] = ["process_document", "CLAIM_MARKER_PREFIX"]
