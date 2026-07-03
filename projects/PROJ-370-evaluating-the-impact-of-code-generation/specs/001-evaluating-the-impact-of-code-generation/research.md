# Research: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

## Research Question
To what extent does LLM-assisted code review (using StarCoder2-3B) correlate with human review quality in detecting bugs, and how do severity classifications differ between the two?

## Dataset Strategy

The study utilizes verified Pull Request datasets from HuggingFace. The spec requires extracting diffs, review comments, and linked issues. The available datasets are:

| Dataset Name | Verified URL | Relevance & Fit |
|:--- |:--- |:--- |
| **prs-v2-sample** | ` | **Primary Source.** Contains PR diffs and metadata. Will be used to extract `diff_text` and `pr_id`. |

**Dataset Fit Analysis:**
- **Required Variables:** `diff_text`, `review_comments` (human annotations), `linked_issue_ids`.
- **Verification:** The `prs-v2-sample` dataset is known to contain PR diffs. However, the specific inclusion of *human review comments* with explicit bug annotations and *linked issue IDs* is not guaranteed.
- **Gap Handling & Heuristics:**
 1. **Linked Issues:** If explicit `linked_issue_ids` are missing, the system will parse the PR description and commit messages for "Fixes #N" or "Closes #N" patterns to infer issue links.
 2. **Human Review Comments:** If explicit bug flags are missing, the system will use a "Bug-Fix Keyword Heuristic" (e.g., presence of "bug", "fix", "error" in comment text) to approximate bug reports.
 3. **Ground Truth Construction (FR-011):** The strict "≥2 independent reviewers" requirement is **not feasible** with standard public datasets. The fallback heuristic is: **A bug is Ground Truth if it is linked to a GitHub issue that is marked as 'closed' or 'merged' in the dataset metadata.** If issue metadata is missing, the PR is flagged as "Unverified" and excluded from the primary ground truth calculation, but included in the "Potential New Bug" analysis.
 4. **Limitation:** If the dataset lacks explicit issue links or closed status, the study will report a "Data Incompleteness" limitation and rely on the "Bug-Fix Keyword Heuristic" with a strong caveat about noise.

## Methodology

### Phase 0: Data Extraction & Preprocessing
1. **Fetch:** Load Parquet files from verified HF URLs.
2. **Checksum:** Generate SHA-256 checksum for the raw file and store in `data/raw/checksums.json` (Constitution Principle III).
3. **Filter:** Select PRs with non-empty diffs. Limit to ≤500 PRs to meet memory constraints (FR-013).
4. **Clean:** Truncate diffs exceeding context window (warning logged). Extract `file_path`, `line_start`, `line_end` from diff headers.
5. **Reviewer Counting:** Count unique authors in `human_review_comments`. If count < 2, flag as "Single Reviewer" (adjusts ground truth logic).
6. **Annotation Generation:** Apply a standardized rubric to human comments to generate `is_bug_report` flags and store in `data/annotations/` (Constitution Principle VI).

### Phase 0.5: LLM Code Detection (FR-016)
1. **Heuristic Scan:** Run a lightweight heuristic (regex for common LLM artifacts, e.g., "Here is the code", "I generated") on the `diff_text`.
2. **Flagging:** Set `is_llm_generated` flag for the PR.
3. **Stratification:** Record the proportion of LLM-generated vs. Human-written code for later subgroup analysis.

### Phase 1: LLM Inference (CPU-Tractable)
1. **Model:** `starcoderbase-3b` (or `bigcode/starcoder2-3b`) loaded in default precision (float32) on CPU.
 - *Constraint:* No 8-bit quantization (`load_in_8bit=False`).
2. **Prompt:** Standardized prompt requesting JSON output: `{"bugs": [{"line_start": int, "line_end": int, "severity": str, "description": str}]}`.
3. **Retry:** Up to 2 retries on JSON parse failure.
4. **Output:** Structured JSON per PR.

### Phase 2: Alignment & Matching
1. **Primary Key:** File path + Line range.
2. **Line-Shift Tolerance:** A match is valid if the LLM's line range overlaps with the human's range **OR** if the LLM's range is within **±5 lines** of the human's range (to account for diff context shifts).
3. **Secondary Key:** Cosine similarity of bug descriptions (threshold ≥ 0.85 default). *Note: Similarity is used only as a tie-breaker; location evidence is primary to avoid text-mimicry bias.*
4. **Strict Rule (FR-012):** Match valid ONLY if `similarity ≥ threshold` AND `Location Overlap ≥ 0.5` (with tolerance).
5. **Sensitivity:** Repeat analysis at thresholds 0.80, 0.85, 0.90 (FR-006).

### Phase 3: Statistical Analysis
1. **Metrics:** Precision, Recall, F1 (vs. Triangulated Ground Truth).
2. **LLM-Only Analysis (FR-017):** Calculate and report "Recall of LLM-Only Detections" (bugs found by LLM, not by humans, but validated against ground truth or flagged as "Potential").
3. **Tests:**
 - **McNemar's Test:** Compare detection rates (LLM vs. Human) on the set of *Reported Bugs*.
 - *Assumption:* The test measures disagreement on *identified* issues, not absolute truth.
 - **Chi-Square Test:** Compare severity distributions (Critical/Major/Minor/Style).
4. **Sensitivity to Noise:** Run tests on a "High Confidence" subset (bugs with explicit issue links) vs. the full set to gauge impact of noisy ground truth.
5. **Reporting:** P-values, Effect Sizes (Cohen's h or Phi), and explicit "Associational" framing (FR-007, FR-014).

## Statistical Rigor & Limitations

- **Multiple Comparisons:** Since sensitivity analysis sweeps 3 thresholds, Bonferroni correction or False Discovery Rate (FDR) will be applied to the resulting p-values if multiple hypothesis tests are reported simultaneously.
- **Power Limitation:** The sample size is capped at 500 PRs due to compute constraints. Power analysis will be performed post-hoc; if underpowered, results will be framed as "preliminary evidence" with wide confidence intervals.
- **Causal Claims:** None. The study design is observational. All claims use "correlate with" or "associated with" (FR-007).
- **Collinearity:** If "LLM-generated code" is a predictor, it is treated as a binary flag. No claim of "independent effect" will be made if LLM code and human code are confounded by PR type.
- **Validity & Circularity:** The validity of the "bug" label depends on the quality of the human review comments in the source dataset. Since the "Human" baseline is derived from the same PR context (comments/issues), it is not an independent ground truth. The study measures **consistency** and **novelty** of detection, not absolute correctness. This limitation is explicitly stated in the final report.
- **Ground Truth Noise:** The "≥2 reviewers" rule is relaxed to "Linked Closed Issue" due to dataset limitations. This may introduce noise, addressed via the "Sensitivity to Noise" analysis.

## Compute Feasibility Plan

- **Runtime:** Target ≤6 hours.
 - Strategy: Process PRs in batches. If a PR exceeds 5 minutes, log timeout and skip (FR-013).
 - Parallelization: Limited to a small number of threads (matching the available CPU runner) to avoid RAM thrashing.
- **Memory:** Target ≤7GB.
 - Strategy: Load model once; process PRs sequentially or in small batches. Stream data from Parquet to avoid loading all into RAM.
- **Disk:** Target ≤14GB.
 - Strategy: Delete intermediate large JSONs after aggregation; keep only derived CSV/Parquet.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use StarCoder2-3B** | Smallest viable model for code understanding; fits in constrained RAM without quantization. |
| **No Quantization** | 8-bit quantization often requires CUDA or specific libraries that may not be stable on free CI; default precision ensures compatibility. |
| **Line-Shift Tolerance** | Prevents false negatives due to minor line number mismatches in diffs. |
| **Triangulated Ground Truth (Fallback)** | Mitigates the risk of single-source error while acknowledging dataset limitations (no explicit maintainer flags). |
| **LLM-Only Reporting** | Ensures FR-017 is met by explicitly tracking and reporting bugs found only by the LLM. |