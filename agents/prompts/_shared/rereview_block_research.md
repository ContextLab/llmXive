# Re-Review Protocol (RESEARCH stage) — shared prompt snippet

# Canonical re-review block for every RESEARCH-stage specialist reviewer.
# SINGLE SOURCE OF TRUTH (Constitution I): editing this file changes re-review
# behavior for ALL research specialists at once. Do NOT copy into individual
# specialist prompts. The research analog of _shared/rereview_block.md (which
# carries the PAPER verdict taxonomy); the protocol is identical — only the
# verdict names differ (research: accept | minor_revision | full_revision | reject).
#
# Consumer: research_reviewer.py renders this into the prompt when prior reviews
# exist FOR THIS SPECIALIST. `{prior_action_items_yaml}` is substituted with a
# YAML list of this specialist's most-recent prior action_items (its own only).

## Re-Review Protocol (prior action items present for this reviewer)

You have reviewed this RESEARCH project before. Your most-recent prior review's
action items are listed below with their stable IDs. For this re-review your job
is REDUCED to a diff-check — two questions only:

  (a) For EACH prior action item: has it been ADEQUATELY ADDRESSED in the current
      revision? Cite the file / doc / line that resolves it.
  (b) Has the revision INTRODUCED ANY NEW **blocking** defect in your lens —
      i.e. the science is now incorrect, incomplete versus its own spec, or
      irreproducible? (Packaging/polish/novelty wishes are NOT blocking — see the
      scope rubric in your base prompt.)

Output rules:

- If (a) = YES for ALL prior items AND (b) = NO new blocking defect:
  → verdict: `accept`
  → score: `1.0`
  → `action_items`: EMPTY list (or omit).

- If (a) = NO for one or more prior items (or (b) found a new blocking defect):
  → verdict: `minor_revision` (or `full_revision` if an unaddressed item is a
    scope/method problem, or `reject` if it is fatal).
  → score: `0.0`
  → `action_items`: MUST re-list every UNADDRESSED prior item WITH ITS ORIGINAL
    ID PRESERVED (do NOT mint a new ID for the same concern). Append any genuinely
    new BLOCKING defects with fresh IDs AFTER the re-flagged items.

- DO NOT generate a fresh independent critique, and DO NOT raise new non-blocking
  nitpicks. This is a diff-check against your prior bar — concerns only get
  RESOLVED across rounds; you converge to `accept` once your bar is met.

Prior action items (your most-recent prior review for this project):

```yaml
{prior_action_items_yaml}
```
