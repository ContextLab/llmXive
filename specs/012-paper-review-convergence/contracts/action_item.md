# Contract: ActionItem

## Purpose

A structured per-concern record emitted by a specialist reviewer. Replaces free-form prose action items in `feedback` with machine-readable items that survive re-review rounds with stable IDs.

## Schema

```yaml
# Embedded in a ReviewRecord's `action_items` list
- id: "a3f1c9b2e5d8"        # 12-char lowercase hex, deterministic from canonicalize(text)
  text: "Add explicit value for hyperparameter β_k in Section 4.1."
  severity: "writing"        # one of: writing | science | fatal
```

## Field rules

| Field | Required | Constraint |
|-|-|-|
| `id` | yes | matches `^[0-9a-f]{12}$`. Reviewers MUST compute via the canonical helper `llmxive.types.action_item_id(text)`. |
| `text` | yes | non-empty, ≤500 chars. Should be a single actionable statement, no compound items. |
| `severity` | yes | exactly one of `writing`, `science`, `fatal`. |

## Severity definitions (canonical — repeated in every paper_reviewer prompt)

- **`writing`** — fixable by editing the manuscript text alone. Examples: typo, jargon, missing citation, unclear caption, terminology drift, formatting inconsistency, redundant paragraph.
- **`science`** — requires modifying the underlying research: re-running an experiment, adding a control, re-analyzing data, reconsidering methodology. Cannot be patched by text edits.
- **`fatal`** — the central claim is unsupportable; the paper cannot be salvaged by any revision. The underlying idea returns to the backlog.

## Validation behavior

- A reviewer that emits `verdict != "accept"` MUST emit `len(action_items) > 0`. The `ReviewRecord` pydantic validator REJECTS records that violate this.
- A reviewer that emits `verdict == "accept"` MAY emit zero action items; non-empty `action_items` on an accept verdict are recorded as informational only and do NOT change the routing.
- ID stability: two reviewers (or the same reviewer across rounds) that flag the SAME concern MUST produce the SAME `id`. The canonicalization in `action_item_id()` is the contract: lowercase, strip punctuation runs, strip section/figure references like `Section \d+\.\d+` and `Figure \d+`, collapse whitespace, sha1 → first 12 hex chars.

## Round-trip example

```python
from llmxive.types import action_item_id, ActionItem

text1 = "Missing value for hyperparameter β_k in Section 4.1."
text2 = "missing value for hyperparameter β_k in Section 4.2."  # different section ref
id1 = action_item_id(text1)
id2 = action_item_id(text2)
assert id1 == id2   # canonicalization absorbs the section-ref diff and the case diff
```

## Anti-patterns

- ❌ Reviewer mints a random UUID for an item that's clearly the same as a prior one — breaks stability gate.
- ❌ Reviewer combines multiple concerns into one action item ("Fix the figure caption AND add the missing citation") — defeats severity classification (one might be writing, the other science).
- ❌ Reviewer omits action items on a non-accept verdict and writes them in free-form `feedback` instead — defeats re-review protocol.
