# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Potential confounding variables (e.g., user‑level effects, time‑of‑day posting patterns) are not modeled or controlled, which may inflate or obscure the observed correlation between control proxy and anxiety.
- "download the public HuggingFace tweet dataset" – the plan specifies using the HuggingFace dataset `cardiffnlp/tweet_sentiment_extraction`, which does **not** contain the required `timestamp` and `user_id` fields needed for the `timestamp_regularity` proxy (AC‑006) and per‑user calculations. Consequently the control‑proxy extraction step cannot be performed as described, violating AC‑005, AC‑006 and the Constitution Principle VI.
