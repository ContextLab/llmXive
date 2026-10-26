# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan uses the “Long‑Context QA (Long‑QA)” dataset (`https://huggingface.co/datasets/llamaindex/long-qa`) as the downstream evaluation benchmark and then filters it to contexts ≥ 32 k tokens. The Long‑QA dataset is not documented to contain such ultra‑long contexts; after filtering it may yield very few or zero examples, which would undermine the QA evaluation (FR‑007) and the associated success criteria (SC‑004). Verify that the chosen dataset actually provides a sufficient number of ≥ 32 k‑token QA instances, or replace it with a verified long‑context QA benchmark (e.g., a filtered subset of HotpotQA or NarrativeQA) that satisfies the length requirement.
