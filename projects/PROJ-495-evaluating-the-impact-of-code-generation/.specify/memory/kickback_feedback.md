# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 9 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Adjusting raw vulnerability counts by dividing by (1‑FPR) and by recall can produce non‑integer, potentially fractional counts, violating the integer‑count assumption of Negative Binomial regression. The plan does not specify how these corrected counts will be rounded or otherwise transformed to satisfy the NB model, nor does it justify that a uniform FP/FN correction is appropriate for all files given possible heterogeneity across languages, file sizes, or tool performance. Clarify the correction procedure (e.g., rounding strategy) and provide justification or validation that the adjusted counts remain suitable for NB GLM.
- FR-010 (assessment of tool‑bias across programming languages) has no corresponding phase or script in the plan.
- SC-008 (reporting of False Positive Rate disparity) is absent from the plan’s SC mapping; no phase claims to satisfy this success criterion.
- Phase 12 runs contract‑validation tests (test_schemas.py) which are not required by any FR or SC in the specification; this constitutes over‑reach.
- The LLM‑generated code corpus is cited as CodeVulnBench but the URL points to https://huggingface.co/datasets/bigcode/codeparrot, which is a generic code‑generation dataset and does not contain curated vulnerability annotations. This mismatch makes the dataset inappropriate for measuring vulnerability density as required by the research question.
- The human‑written code substitute is cited as the verified JavaScript dataset (https://huggingface.co/datasets/hchautran/javascript). This dataset is a generic collection of JavaScript files and is not a vetted, vulnerability‑rich corpus (e.g., Juliet). Using it as the human baseline may yield an unrepresentative comparison and violates the requirement for a comparable human‑written code benchmark.
- The plan assumes the entire CodeVulnBench and JavaScript datasets can be processed on a GitHub Actions free‑tier runner (CPU‑only, ≤6 h, ≤7 GB RAM). CodeVulnBench (codeparrot) contains millions of files and the SonarQube Docker image alone exceeds the runner’s memory limits, making the end‑to‑end execution infeasible under the stated resource constraints.
- The Constitution Check table lists a placeholder SHA‑256 (`d41d8cd98f00b204e9800998ecf8427e`) for the human‑code dataset. Principle II (Verified Accuracy) requires that every external citation be verified with a real checksum; a placeholder does not satisfy this requirement.
- The plan specifies the audit sample size as `min(0.10 * total_findings, 200)` with a lower bound of 100, whereas FR‑007 in the spec defines the sample size as `min([deferred] of total findings, 100 samples)`. This discrepancy creates a conflict between the plan and the specification.
