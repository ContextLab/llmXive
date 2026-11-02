# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Spec FR-001 requires ingestion of raw text transcripts and associated labels. The plan only ingests pre‑computed sentence embeddings and creates a CSV with an empty `text` field, citing that raw transcripts are unavailable. This does not satisfy the functional requirement to ingest raw transcripts.
- Spec FR-002 mandates extraction of lexical, syntactic, **and** semantic features. The plan extracts only the semantic coherence feature and sets all lexical/syntactic features to `null`, which fails to meet the requirement for full feature extraction.
- The plan relies exclusively on the ADReSS Challenge *sentence‑embedding* dataset, which contains only pre‑computed embeddings and no raw transcripts. Functional Requirement FR‑001 explicitly requires ingestion of raw text transcripts (and associated labels) to enable lexical and syntactic feature extraction. Using a dataset that lacks the necessary raw text makes the dataset inappropriate for the stated requirement and undermines the ability to compute the required lexical/syntactic markers.
- The success criterion SC‑002 demands ≥ 1000 usable records, yet the ADReSS embedding dataset provides only a few hundred participants (≈ 300 after exclusions). The plan attempts to amend the criterion to “≥ 300 records” without a formal spec amendment, which conflicts with the original specification and renders the success criterion unattainable with the cited dataset.
