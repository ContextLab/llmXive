"""T001 — verify package (spec 018): per-claim verification modes.

Re-exports the primary public symbols from each sub-module so callers
can do ``from llmxive.verify import select_mode`` etc.
"""

from llmxive.verify.mode import select_mode
from llmxive.verify.compute import verify_computational
from llmxive.verify.constants import true_value
from llmxive.verify.approximate import is_valid_rounding

__all__ = [
    "select_mode",
    "verify_computational",
    "true_value",
    "is_valid_rounding",
]
