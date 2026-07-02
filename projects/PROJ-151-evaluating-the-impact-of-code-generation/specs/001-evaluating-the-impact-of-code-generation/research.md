# Research: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Problem Statement

Do LLM-generated code snippets require more reviewer effort (time, comments, difficulty) than human-written snippets for the same task? The historical data lacks ground-truth time/difficulty, so we use `filtered_comment_count` as a proxy for the historical analysis (Exploratory) and validate findings via a human survey study (Confirmatory).

## Dataset Strategy

### Historical Data (Gerrit Chromium Proxy)
- **Source**: `loubnabnl/prs-v2-sample` (Verified URL: `)
- **Content**: PR metadata, code diffs, review comments.
- **Constraints**:
 - **No `review_time` or `perceived_difficulty`**: Explicitly excluded per FR-001.
 - **Proxy**: `filtered_comment_count` (after quality filter) used for historical effort modeling.
 - **Filter**: Java/Python only, ≤30 LOC changed.
- **Fit Check**: The dataset contains code snippets and comment counts. It **does not** contain the required `review_time` or `perceived_difficulty` fields. This mismatch is explicitly handled by:
 1. Using `filtered_comment_count` as the primary proxy for historical analysis (Exploratory).
 2. Designing a separate **Validation Study** (FR-012) to measure actual effort on a subset of generated code (Confirmatory).
- **Adaptive Sample**: If the filtered dataset yields < 1,000 rows, the study proceeds with available N, but power analysis (Phase 0.5) adjusts model complexity.

### Generated Data
- **Source**: Synthesized via CodeGen-350M (primary) / StarCoder-1B (secondary) on CPU.
- **Fit Check**: Generated code is matched to problem statements extracted from PR titles. **Symmetric Prompting** is used: the exact same extracted text is used for both Human (as-is) and LLM groups to isolate 'Origin' from 'Prompt Quality'.

### Validation Study Data
- **Source**: Human reviewers (≥3) via browser-based tool.
- **Content**: Actual review time (ms), comment count, 5-point Likert difficulty.
- **Fit Check**: Directly addresses the missing ground-truth fields in the historical dataset.

## Methodology

### Phase 0: Setup & Power Analysis (FR-009, FR-003)
1. Initialize environment, pin seeds (42).
2. **Phase 0.5: Power Analysis**:
 - Count unique `project_id` clusters.
 - Estimate power for mixed-effects model (interaction term).
 - **Decision**: If clusters < 30, switch to Fixed-Effects model with robust SEs. If N < 100, reduce sample size target to 200.

### Phase 1: Data Ingestion & Filtering (FR-001, FR-002)
1. Download `prs-v2-sample` via `datasets.load_dataset`.
2. Filter for `language` in ["Java", "Python"].
3. Filter for `diff_lines` ≤ 30.
4. **Phase 1.5: Comment Quality Filter**:
 - Exclude comments with length < 10 chars or containing only 'LGTM', 'nit', 'n/a'.
 - Recalculate `comment_count` as `filtered_comment_count`.
5. Validate presence of `code_snippet` and `filtered_comment_count`.
6. Output: `data/processed/filtered_prs.parquet`.

### Phase 2: Code Generation (FR-002, FR-003)
1. Extract problem statement from PR title (Symmetric).
2. Load a CodeGen model (CPU, float16).
 - **Fallback**: If OOM, switch to StarCoder-1B (if memory allows) or reduce N.
3. Generate code with seed=42.
4. **Phase 2.5: Plausibility Filter**:
 - Check for non-existent imports, trivial solutions, or infinite loops.
 - Exclude failed generations.
5. Log provenance (model, prompt, seed, timestamp) to `data/generated_provenance.csv`.
6. Output: `data/generated/code_snippets.csv`.

### Phase 3: Metric Computation (FR-004)
1. Compute for both human and generated code:
 - Cyclomatic Complexity (Radon)
 - Maintainability Index (Radon)
 - Pylint Score (Python)
 - Checkstyle Score (Java)
 - Token Count
2. Output: `data/processed/metrics.csv`.

### Phase 4: Statistical Analysis (FR-005, FR-006, FR-007, FR-010, FR-013, FR-014)
1. **Phase 3.5: Collinearity & Distributional Shift Check**:
 - Perform KS-test on Complexity distributions (Human vs. Generated).
 - If significant shift, use Propensity Score Matching (PSM) or Stratified Analysis.
2. **Phase 4.1: Mixed-Effects Model**:
 - Fit model: `Effort ~ Complexity + Origin + (Complexity * Origin) + (1|Project_ID)`.
 - If clusters < 30, use Fixed-Effects model.
3. **Phase 4.2: Interaction Test**:
 - If `Origin * Complexity` is significant (p < 0.05), report stratified results.
4. **Phase 4.3: Wilcoxon Signed-Rank Test**:
 - Compare predicted effort for matched pairs (Human vs. Generated) per FR-010.
5. **Phase 4.4: Multiple-Comparison Correction**:
 - Apply Bonferroni/FDR for all hypothesis tests per FR-007.
6. **Phase 4.5: Sensitivity Analysis**:
 - Sweep LOC thresholds (15, 30, 50) per FR-006.
7. **Phase 4.6: Validation Study & Transfer Error**:
 - Analyze survey data (Likert, time).
 - Calculate Cohen's Kappa (FR-011).
 - Compute MAE between predicted (historical) and actual (validation) effort per FR-014.
8. **Phase 4.7: Success Criterion Check**:
 - Evaluate Pearson r ≥ 0.7 (SC-005).
 - Report Pass/Fail.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni/FDR correction applied to all >1 hypothesis tests (FR-007).
- **Sample Size/Power**:
 - Historical: N≥1000 (adaptive).
 - Validation: N≥50 (target power ≥ 0.70 if fallback triggered).
 - **Power Analysis**: Performed in Phase 0.5. If clusters < 30, model switches to Fixed-Effects.
- **Causal Claims**: **None**. All findings framed as associational (FR-005). Explicit disclaimer included in final report.
- **Measurement Validity**: `filtered_comment_count` is a weak proxy; historical results are exploratory. Validation study is confirmatory.
- **Collinearity**: Addressed via KS-test (Phase 3.5) and PSM/Stratification fallback.
- **Prompt Quality**: Addressed via Symmetric Prompting (same input for both groups).

## Compute Feasibility

- **Hardware**: GitHub Actions Free (CPU, 7 GB RAM).
- **Strategy**:
 - **Primary Model**: CodeGen-350M (CPU, float16).
 - **Secondary Model**: StarCoder-1B (only if memory allows).
 - Use `torch` CPU wheel.
 - Process in batches to avoid OOM.
- **Runtime**: Target ≤ 6 hours.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| StarCoder OOM on CPU | Pipeline failure | Primary model is CodeGen-350M; StarCoder is secondary. |
| Low generation success rate | Insufficient data | Plausibility filter; log failures; report rate. |
| Weak `comment_count` correlation | Invalid historical model | Reliance on validation study for final conclusions; historical results are exploratory. |
| Reviewer bias in survey | Invalid difficulty rating | Blinding protocol (reviewers unaware of origin). |
| Low cluster count (Power) | Invalid mixed-effects | Switch to Fixed-Effects with robust SEs. |
| Distributional Shift (Collinearity) | Spurious interaction | Use PSM or Stratified Analysis. |
| Prompt Quality Confound | Invalid Origin effect | Symmetric Prompting (same input for both groups). |
| Semantic Correctness | Invalid comparison | Plausibility Filter (static analysis) applied to both groups. |