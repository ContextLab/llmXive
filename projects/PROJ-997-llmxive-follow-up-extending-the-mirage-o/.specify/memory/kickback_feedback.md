# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The task T015 allows automatic off‑load of the quantized inference step to a free Kaggle GPU when the CPU run exceeds 5 h or OOM. This violates Constitution Principle VI, which mandates that ground‑truth KL divergence be measured using a **CPU‑based** quantized engine. Off‑loading to GPU weakens FR‑002 (CPU‑based quantized inference) and FR‑003 (hardware‑grounded KL calculation). The verification also permits `hardware_source` to be either "CPU" or "GPU", further contradicting the principle.
- The verification description for T016 mistakenly references `code/cli/generate_ground_truth.py` instead of the intended `code/cli/validate_dataset_stats.py`. This is a typographical inconsistency that should be corrected.
