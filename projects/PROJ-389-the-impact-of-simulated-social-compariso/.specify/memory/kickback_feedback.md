# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan defines `exposure_level` as “proportion of comments from target subreddits” (task 4) and `self_eval_score` as “sentiment‑adjusted first‑person pronoun ratio” (task 8). Both metrics are computed from the same Reddit comment stream belonging to the user. This violates Constitution Principle VI (Distinct Data Stream Integrity) because the predictor (`exposure_level`) is not derived from an independent exposure stream but from the user’s own comments, which also generate the outcome (`self_eval_score`). Consequently the validation of moderation effects is circular: the predictor is partially a summary of the outcome data, making any regression result tautological rather than an independent test of a psychological mechanism.
