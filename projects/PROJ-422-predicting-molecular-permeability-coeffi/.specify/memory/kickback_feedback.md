# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Power analysis uses a fixed effect size (Cohen’s d = 0.3) and records `planned_sample_size` and `achieved_power`, yet the pipeline continues even when `sufficient: false`. Proceeding under‑powered undermines the ability to detect the claimed performance gap.
- The plan’s Phase 0 checks for a column named `permeability` in the listed verified datasets, but none of the cited datasets actually contain an experimental permeability column (or any approved surrogate). Consequently the pipeline will always halt and open a GitHub issue, violating FR‑001 which requires the system to acquire at least one public dataset with a valid permeability target (or an approved surrogate). Without an appropriate target dataset the research question cannot be answered.
- The plan asserts compliance with Principle II by stating “Only URLs listed in the ‘Verified datasets’ block are used; no new citations introduced.” However, the plan document does not contain a ‘Verified datasets’ block that enumerates the allowed URLs, making the claim ambiguous and potentially non‑compliant with the constitution’s Verified Accuracy requirement.
