# Re-Review Protocol — shared prompt snippet

# This is the canonical re-review prompt block consumed by every paper-stage
# reviewer prompt. SINGLE SOURCE OF TRUTH (Constitution I): editing this file
# changes the re-review behavior for ALL specialists at once. Do NOT copy this
# text into individual specialist prompts.
#
# Consumers (rendered into the user prompt by `paper_reviewer.py` when prior
# reviews exist FOR THIS SPECIALIST):
#   - agents/prompts/paper_reviewer.md           (lead)
#   - agents/prompts/paper_reviewer_*.md         (12 specialists)
#
# The `{prior_action_items_yaml}` placeholder is substituted at render time
# with a YAML list of the most-recent prior review's action_items (this
# specialist's only — not other specialists' priors).

## Re-Review Protocol (prior action items present for this reviewer)

You have reviewed this paper before. Your most-recent prior review's action
items are listed below with their stable IDs. For this re-review, your job is
REDUCED to two questions:

  (a) For EACH prior action item: has it been ADEQUATELY ADDRESSED in the
      current revision?
  (b) Has the revision INTRODUCED ANY NEW ISSUES?

Output rules:

- If (a) = YES for ALL prior items AND (b) = NO new issues:
  → verdict: `accept`
  → score: `0.5`
  → `action_items`: EMPTY list (or omit).

- If (a) = NO for one or more prior items:
  → verdict: `minor_revision` (or `major_revision_writing` if any unaddressed
    item is writing-class, `major_revision_science` if science-class, or
    `fundamental_flaws` if fatal-class).
  → score: `0.0`
  → `action_items`: MUST contain the unaddressed items WITH THEIR ORIGINAL
    IDs PRESERVED (do NOT mint new IDs for re-flags of the same concern).
    Append any NEW issues with fresh IDs AFTER the re-flagged items.

- DO NOT generate a fresh independent critique. This is a diff-check against
  the prior bar, not a full review.

Prior action items (your most-recent prior review for this paper):

```yaml
{prior_action_items_yaml}
```
