# Feature Specification: Evaluating the Impact of Code Generation Models on Code Testability

**Feature Branch**: `001-evaluating-the-impact-of-code-generation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation Models on Code Testability"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1)

The system MUST download a matched subset of HumanEval tasks, generate code for each task using the specified LLM, execute static analysis tools (`radon`) to compute cyclomatic complexity and Halstead metrics, and run the generated code together with the human reference solution against the HumanEval test suites while collecting **actual branch coverage %** via `coverage.py` (invoked through `pytest --cov`). This creates a paired dataset for downstream statistical comparison.

**Why this priority**: Accurate, paired data (human vs. LLM for the same task) is essential for a statistically valid comparison of testability.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that a JSON report is produced containing `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every task where both human and LLM solutions are present, with at least 40 valid paired samples (n ≥ 40) and no missing fields for processed samples.

**Acceptance Scenarios**:

1. **Given** the HumanEval dataset is available on HuggingFace, **When** the system executes the download and generation script, **Then** A subset of task IDs is selected and stored locally. For each task, the LLM generation is attempted up to 3 retries; successful generations are paired with the human solution.
2. **Given** the paired code samples are stored locally, **When** `radon` and `pytest --cov` are invoked, **Then** a structured output containing `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct` (recorded as `[deferred]` if execution fails), and `pass_rate` (0 or 1) is produced for every valid pair.

---

### User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

The system MUST perform appropriate statistical tests on the paired dataset: Wilcoxon Signed‑Rank for continuous metrics (complexity, Halstead, branch coverage) and McNemar’s test for the binary pass‑rate outcome. For unpaired exploratory checks, Fisher’s Exact Test may be used. The system MUST also conduct an a priori power analysis (effect size d = 0.5, α = 0.05, power ≥ 0.8) and a post‑hoc power check.

**Why this priority**: This directly answers whether LLM‑generated code differs in testability from human code, using statistically sound methods and justified sample size.

**Independent Test**: Feed two mock paired datasets with known differences; the system must output p‑values < 0.05 for the continuous metrics (using Wilcoxon) and correctly flag a significant difference in pass‑rate via McNemar’s test. The power analysis report must show required n ≥ 38 and confirm that the actual n ≥ 40 meets this target.

**Acceptance Scenarios**:

1. **Given** paired arrays of complexity scores, **When** the Wilcoxon Signed‑Rank test is executed, **Then** a p‑value is returned and the result is flagged “significant” if p < 0.05.
2. **Given** paired binary pass‑rate outcomes, **When** McNemar’s test is executed, **Then** a p‑value is returned and the result is flagged accordingly.
3. **Given** the statistical results, **When** the system generates the summary report, **Then** the report explicitly states the null hypotheses, conclusions, and both a priori and post‑hoc power analysis outcomes.

---

### User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

The system MUST generate visual comparisons (histograms and boxplots) of all continuous metric distributions, compile a fully automated markdown report summarizing statistical findings, and perform a sensitivity analysis using a larger model (`CodeLlama‑7B`) accessed via the HuggingFace Inference API (fallback to `CodeLlama‑3B` if unavailable). All steps must be reproducible without manual intervention.

**Why this priority**: Visualizations aid interpretation; the automated report satisfies reproducibility; sensitivity analysis evaluates robustness across model scales.

**Independent Test**: Verify that `matplotlib` creates PNG files for each metric, that the Jinja2‑based script produces `results_report.md` containing all figures, statistical tables, and sensitivity analysis results, and that the API call successfully retrieves CodeLlama‑7B outputs (or falls back gracefully).

**Acceptance Scenarios**:

1. **Given** the statistical test results and raw metric data, **When** the reporting script runs, **Then** `results_report.md` is generated with histograms, boxplots, a table of test statistics, p‑values, and power analysis summaries.
2. **Given** the report is generated, **When** a reviewer inspects it, **Then** the document clearly states mean/median values for each metric, significance decisions, and the outcome of the sensitivity analysis (including any differences observed with the larger model).

### Edge Cases

- If `Salesforce/codegen-350M-mono` fails to generate valid Python code for a task after 3 retries, the task is marked as a missing LLM sample; the human solution remains, and the pair is excluded from paired analyses but counted toward the overall download target. Coverage for the failed LLM sample is recorded as **[deferred]** and logged.
- If `coverage.py` (via `pytest --cov`) cannot execute a sample due to runtime errors, coverage for that sample is recorded as **[deferred]** and the error is logged; the sample still participates in paired analyses only if the human side is valid, but the pair is excluded from the paired test if the LLM side is invalid.
- If the HumanEval dataset version on HuggingFace changes, the system pins the exact commit hash used (recorded in `state/dataset.yaml`) to ensure reproducibility.
- If the HuggingFace Inference API for CodeLlama‑7B is unavailable, the system automatically falls back to `CodeLlama‑3B` and notes the substitution in the report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a matched subset of **exactly 50** HumanEval task IDs from HuggingFace, verify dataset integrity via SHA256 checksum, and store them locally. (See US-1)
- **FR-002**: System MUST generate up to 50 LLM code samples using `Salesforce/codegen-350M-mono` on a CPU‑only environment, retrying each failed generation up to **3** times. Generation must be paired with the same task IDs as the human solutions; if generation ultimately fails, the pair is excluded from paired analyses to prevent selection bias. (See US-1)
- **FR-003**: System MUST compute **cyclomatic complexity**, **Halstead volume**, and **actual branch coverage %** for each **valid** code sample by running `radon` and `pytest --cov` during test execution. For any sample that fails execution, branch coverage is recorded as **[deferred]** and the failure is logged. (See US-1)
- **FR-004**: System MUST perform statistical hypothesis testing on the paired dataset:
  - Wilcoxon Signed‑Rank test for continuous metrics (complexity, Halstead, branch coverage).
  - McNemar’s test for the paired binary pass‑rate.
  - Fisher’s Exact Test for any unpaired binary comparison.
  - All tests must use a two‑tailed α = 0.05 significance threshold.
  - The analysis must explicitly test the independence of structural complexity from functional success, acknowledging potential correlation but treating them as distinct variables. (See US-2)
- **FR-005**: System MUST execute each generated and human code sample against its HumanEval test suite, record a binary **pass_rate** (1 = all tests passed, 0 = any failure), and capture coverage simultaneously as described in FR-003. (See US-2)
- **FR-006**: System MUST generate a fully automated markdown report (`results_report.md`) using a Jinja2 template populated with all figures, tables, statistical conclusions, power analysis results, and sensitivity analysis outcomes. No manual editing is permitted. (See US-3)
- **FR-007**: System MUST log all generation failures, parsing errors, execution failures, and coverage‑zero assignments to `errors.log` with timestamps and task IDs. (See US-1)
- **FR-008**: System MUST conduct an **a priori** power analysis (effect size d = 0.5, α = 0.05, power ≥ 0.8) before data collection to determine the sample size target (n ≥ 38) and a **post‑hoc** power check after analysis to validate achieved power based on observed effect sizes, reporting both in the final document. (See US-2)
- **FR-009**: System MUST perform a sensitivity analysis by generating additional code samples for the same task set using **CodeLlama‑7B** via the HuggingFace Inference API. The system MUST use 4‑bit quantization to fit the model in 7GB RAM; if 4-bit quantization fails, fall back to **CodeLlama‑3B**. Results are compared to the primary model and reported. (See US-3)
- **FR-010**: System MUST invoke the Reference‑Validator Agent to verify the accuracy of all external URLs and paper citations before any analysis begins, aborting the pipeline on validation failure. (See US-2)
- **FR-011**: System MUST update the `state/` YAML file with SHA256 hashes of the downloaded HumanEval dataset and all generated model artifacts (including CodeLlama outputs) upon successful pipeline completion. (See US-1)

### Key Entities

- **CodeSample**: Represents a single unit of code (human reference or LLM generated) linked to a HumanEval task ID, with attributes: `source_type`, `raw_code`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, `pass_rate`.
- **MetricResult**: Holds the computed structural properties for a `CodeSample` used as input for statistical testing.
- **StatisticalTestResult**: Contains test name, statistic, p‑value, and conclusion for each hypothesis test.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: At least **40** valid paired samples (human + LLM) are obtained (≥ 80 % of the 50‑task target). (See US-1)
- **SC-002**: Statistical significance is evaluated using the correct tests (Wilcoxon, McNemar, Fisher) with α = 0.05; results are considered significant only if p < 0.05. (See US-2)
- **SC-003**: The final report includes all required visualizations (histograms, boxplots), tables of test statistics, p‑values, power analysis outcomes, and a discussion of the correlation between structural metrics and pass_rate. (See US-3)
- **SC-004**: The pipeline completes without manual intervention; all steps are executed by code only. (See US-3)
- **SC-005**: All external citations are validated by the Reference‑Validator Agent before analysis begins. (See US-2)
- **SC-006**: The a priori power analysis shows that the planned sample size (n ≥ 38 pairs) achieves ≥ 0.8 power for effect size d = 0.5; the post‑hoc analysis confirms achieved power ≥ 0.8 based on observed effects. (See US-2)
- **SC-007**: Sensitivity analysis results (CodeLlama‑7B with 4-bit quantization or fallback CodeLlama‑3B) are included in the report, with a clear comparison to the primary model’s metrics. (See US-3)
- **SC-008**: The `state/` YAML file contains correct SHA256 hashes for the HumanEval dataset and all generated artifacts. (See US-1)

## Assumptions

- The `Salesforce/codegen-350M-mono` model can be loaded and run within the limited RAM (≈ 7 GB) of the GitHub Actions free‑tier runner without GPU acceleration.
- The HumanEval dataset on HuggingFace remains accessible and stable; the specific commit hash used is recorded for reproducibility.
- The `radon` and `coverage.py` libraries are compatible with the Python version on the runner and do not require compiled C extensions.
- Structural metrics (complexity, Halstead) are treated as predictors of testability; the study will assess their correlation with actual pass‑rate and coverage, not assume independence.
- The effect size d = 0.5 for the a priori power analysis is based on prior literature on code quality differences between human and LLM‑generated code (see *Zhou et al., 2023*). The study acknowledges a risk of Type II error if the observed effect size is smaller than 0.5.
- The HuggingFace Inference API for CodeLlama‑7B provides sufficient latency and throughput for the limited number of sensitivity‑analysis samples; if unavailable, the fallback to CodeLlama‑3B maintains feasibility.
- All verification (statistical, citation, artifact hashing) is fully automated; no manual steps are required after pipeline start.
- The a priori power analysis determines the sample size target (n ≥ 38) before data collection, while the post-hoc analysis is strictly for validating the achieved power after data collection; the former does not rely on the latter.