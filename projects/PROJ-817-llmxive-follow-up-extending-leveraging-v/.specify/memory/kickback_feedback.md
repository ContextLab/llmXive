# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan cites three InstructPix2Pix parquet shards as the raw prompt source (see ‘Download & verify three open InstructPix2Pix parquet shards (balanced 1 000‑prompt set)’). InstructPix2Pix provides single‑step editing instructions and does not contain naturally occurring *conflicting* instructions required to evaluate the hypothesis that a symbolic constraint‑graph layer mitigates degradation on *conflicting* prompts. Using this dataset risks an invalid test of the core research question; a dataset explicitly containing multi‑step or contradictory editing instructions (or a curated subset with verified conflicts) is needed.
- The plan describes collecting human feasibility scores for all 1 000 prompts but never names the concrete artifact defined in the data model (`human_validation.csv`). Adding an explicit reference to this file (e.g., “writes `data/results/human_validation.csv`”) would align the plan with the data‑model.
- FR-001 requires human feasibility scores for *all* 1 000 prompts, but FR-009 only mandates collection for at least 200 prompts. The plan assumes 500 conflicting prompts have human scores for paired tests and power analysis (see Research §8), which is inconsistent with the lower annotation budget. This mismatch may leave the study under‑powered and invalidate the planned statistical conclusions.
- FR-009’s minimal 200‑prompt annotation contradicts the plan’s reliance on a full 1 000‑prompt human‑annotated dataset for the primary paired analysis. Without sufficient human ground‑truth data, the paired t‑test/Wilcoxon comparison and the claimed power (≈0.85) cannot be justified.
