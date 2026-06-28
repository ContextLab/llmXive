# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 14 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-006 requires reporting (a) false-positive rate AND (b) inconsistency rate (proportion of datasets where significance status changes). T042 covers FPR calculation but does not explicitly tag the inconsistency rate metric. Add a task or clarify that inconsistency rate is computed within T034-T036 comparison logic.
- Tasks T020-T024 are all marked [P] (parallel-safe) but all write to the same file (code/cleaning.py). Multiple tasks modifying the same file cannot run in parallel safely. Either split into separate files or remove [P] tags.
- Tasks T034-T036 are all marked [P] (parallel-safe) but all write to the same file (code/reporting.py). Multiple tasks modifying the same file cannot run in parallel safely. Either split into separate files or remove [P] tags.
- Spec claims each user story is 'independently shippable' but dependencies section states US2 'Depends on US1 baseline metrics' and US3 'Depends on US1 and US2 completion'. This contradicts the independent-shippable-unit requirement for user-story groups.
- T004 creates utils.py, T007 configures logging in code/utils.py. T007 should precede T004 or be integrated into it, not come after the file is already created.
- Validation and logging tasks (T014, T016, T028-T030, T049-T050) are separated from their implementation tasks. These should be integrated into the implementation tasks they validate, not standalone tasks that create artificial ordering dependencies.
- T005 'Setup environment configuration management (env vars for dataset URLs, output paths)' lacks concrete deliverable. Specify file path (e.g., code/config.py or .env.example) and exact variables to define.
- T053 'Performance optimization (ensure ≤6 hours runtime, reduce bootstrap iterations if needed)' is too coarse. Split into: (a) add runtime profiling/logging, (b) implement conditional bootstrap reduction logic with threshold.
- T039 uses [deferred] markers for missingness bins (0-[deferred], 5-[deferred], 10-[deferred]). While sanctioned per spec 020/023, the task should reference where these values will be resolved (e.g., 'per research.md or spec update').
- T046-T048 compute median/IQR across datasets per plan.md:Dataset Feasibility Notice (only 2 datasets available). Task should note statistical limitation or defer until dataset count increases per SC-006 kickback.
- Tasks proceed with 2 verified datasets (UCI HAR, UCI Shopper) while SC-006 requires ≥10 datasets. Plan.md explicitly flags this as 'BLOCKING GAP - SC-006 requires kickback to spec author' but tasks implement median/IQR calculations (T046-T048) on only 2 datasets, which is statistically invalid per plan feasibility notice.
- T040 implements bootstrap with '≥1000 resamples per dataset' which preserves Constitution Principle VI (minimum 1000 iterations). However, plan assumptions allow reduction to 500 if CPU constraints hit. Tasks should explicitly document this fallback path to preserve plan flexibility while maintaining constitution minimum.
- T037 implements Benjamini-Hochberg correction correctly (q ≤ 0.05). Spec FR-007 incorrectly states 'family-wise error rate' (BH controls FDR, not FWER). Plan correctly notes this. Tasks should not repeat the spec's error - current wording is acceptable but could be more precise.
- T011 specifies 'UCI HAR, UCI Shopper' only, deviating from spec FR-001 which requires 'OpenML Small Datasets collection'. Plan.md notes this deviation as 'Deviation: OpenML has NO verified source; adapted to UCI HAR/Shopper only. Spec requires kickback.' Tasks should explicitly acknowledge this spec deviation rather than silently proceeding.
