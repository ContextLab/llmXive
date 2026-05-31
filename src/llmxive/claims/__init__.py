"""claims package — claim-verification layer (spec 016).

Re-exports land here as the sub-modules are implemented.
"""

from __future__ import annotations

from llmxive.claims.gate import CLAIM_MARKER_PREFIX  # T010
from llmxive.claims.service import process_document  # T017

__all__: list[str] = ["CLAIM_MARKER_PREFIX", "process_document"]
