# Feature Specification: Evaluating the Impact of Code Generation Models on Code Testability

**Feature Branch**: `294-evaluating-the-impact-of-code-generation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Evaluate the impact of code generation models on code testability"

## User Stories

### US1: Data Acquisition, Generation, and Metric Computation Pipeline (Priority: P1)
As a researcher, I want to download the HumanEval dataset (pinned to a specific commit hash), generate code using the Primary Model (Salesforce/codegen-mono), execute test suites to record pass rates, and compute structural metrics (Complexity, Halstead, Branch Coverage Potential) so that I can create a paired JSON dataset for analysis.

**Why this priority**: This is the foundational data pipeline required for all subsequent analysis. Without valid, pinned data and computed metrics, no statistical comparison is possible.  
**Independent Test**: Can be fully tested by running the download and generation scripts and verifying the existence of `data/generated/human_samples.json` and `data/generated/codegen_samples.json` with valid SHA256 hashes.  
**Acceptance Scenarios**:
1. **Given** a valid internet connection, **When** the download script runs, **Then** the HumanEval dataset is saved to `data/raw/humaneval.parquet` with a matching SHA256 checksum for the pinned commit.
2. **Given** the dataset is loaded, **When** the generation script runs, **Then** `data/generated/codegen_samples.json` contains valid code strings for all 164 tasks.
3. **Given** generated code, **When** the analysis script runs, **Then** a metrics JSON file is produced containing `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_potential`, and `pass_rate` for each task.

---

### US2: Paired Statistical Comparison and Sensitivity Analysis (Priority: P2)
As a researcher, I want to perform Wilcoxon Signed-Rank tests on the structural metrics between Human and LLM code and conduct a sensitivity analysis using a quantized CodeLlama model so that I can validate the statistical significance and robustness of the findings.

**Why this priority**: This addresses the core research question of whether LLMs alter testability. The sensitivity analysis ensures findings are not artifacts of a single model family.  
**Independent Test**: Can be fully tested by running the statistical analysis module on the generated metrics and verifying the output of p-values and MDES calculations.  
**Acceptance Scenarios**:
1. **Given** paired metrics (Human vs. LLM), **When** the test script runs, **Then** a Wilcoxon Signed-Rank test is performed and a p-value < 0.05 is reported if a significant difference exists.
2. **Given** the fixed sample size (N=164), **When** the sensitivity analysis runs, **Then** the Minimum Detectable Effect Size (MDES) is calculated for alpha=0.05 and power=0.80.

---

### US3: Visualization, Reporting, and Validation (Priority: P3)
As a researcher, I want to generate automated Markdown reports with figures, validate all citations using the Reference-Validator Agent, and track artifact integrity so that I can communicate findings effectively and ensure reproducibility.

**Why this priority**: This ensures the research outputs are communicable, verifiable, and reproducible.  
**Independent Test**: Can be fully tested by running the report generator and verifying the presence of `report.md`, `figures/`, and `artifact_hashes.yaml`.  
**Acceptance Scenarios**:
1. **Given** the analysis results, **When** the report generator runs, **Then** a Markdown report is produced with figures comparing Human vs. LLM metrics.
2. **Given** a report with citations, **When** the validation step runs, **Then** all citations are verified as valid and reachable.

## Functional Requirements

- **FR-001**: System MUST download the HumanEval dataset and verify SHA256 checksums against a **specific commit hash** (not just a tag) to ensure bit-for-bit reproducibility (See US1).
- **FR-002**: System MUST generate code using Salesforce/codegen-mono with exponential-backoff retry logic and a 60-second timeout per task (See US1).
- **FR-003**: System MUST calculate cyclomatic complexity and Halstead volume using the `radon` tool, ensuring all outputs are floats ≥ 0 (See US1).
- **FR-004**: System MUST perform statistical hypothesis testing using the **Wilcoxon Signed-Rank test** (paired) with a significance level (alpha) of **0.05** and the null hypothesis that the median difference in metrics is zero (See US2).
- **FR-005**: System MUST execute test suites using the HumanEval harness with a **60-second timeout** and record `pass_rate` (passed_tests / total_tests); tasks with `pass_rate` < **0.80** must be filtered out to ensure functional correctness before structural analysis, explicitly distinguishing this execution filter from the static `branch_coverage_potential` metric (See US1).
- **FR-006**: System MUST generate Markdown reports with figures comparing Human and LLM metrics (See US3).
- **FR-007**: System MUST setup logging with timestamp and task ID tracking (See US1).
- **FR-008**: System MUST implement **Sensitivity Analysis (MDES)** replacing A Priori power analysis, calculating the Minimum Detectable Effect Size for N=164 at alpha=0.05 and power=0.80 to validate the statistical power of the fixed sample size (See US2). *Justification: Required to confirm N=164 is sufficient for the research question.*
- **FR-009**: System MUST implement sensitivity analysis using **CodeLlama-3B-Quantized** (CPU-feasible) to compare metric variance across model families; success is defined as detecting variance > 0.05 in complexity metrics (See US2). *Justification: Required to validate robustness across model families, addressing the 'Related Work' gap.*
- **FR-010**: System MUST validate citations in generated reports using **Reference-Validator Agent checks** to ensure URL reachability and title overlap (See US3).
- **FR-011**: System MUST track artifact integrity for **all files in data/analysis/** by storing a valid SHA256 hash in `artifact_hashes.yaml` (See US3).

## Data Model

- **Metrics JSON**: Contains `cyclomatic_complexity` (float), `halstead_volume` (float), `branch_coverage_potential` (float, static analysis), and `pass_rate` (float, execution).
- **Artifact Hashes**: YAML file tracking checksums of all generated artifacts in `data/analysis/`.
- **Human Samples**: JSONL file containing reference solutions extracted from the pinned HumanEval dataset.
- **LLM Samples**: JSONL file containing generated code from the Primary and Sensitivity models.

## Success Criteria

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task-completion time is measured against the documented capacity requirement (See US1).
- **SC-002**: Throughput under load is measured against the documented capacity requirement (See US1).
- **SC-003**: Primary-task success rate (pass_rate) is measured against the prior workflow's observed rate (See US1).
- **SC-004**: Support-ticket volume for [X] is measured against the pre-change trailing average (See US3).
- **SC-005**: **MDES is calculated** for N=164, alpha=0.05, power=0.80; the result is reported as the minimum effect size detectable (See FR-008).
- **SC-006**: **Variance in complexity metrics** is measured across Primary and Sensitivity models; a variance > 0.05 is reported as a significant sensitivity (See FR-009).

## Assumptions

- Users have stable internet connectivity for dataset download.
- Mobile support is out of scope for v1.
- Existing authentication system will be reused (N/A for this research tool).
- Requires access to the existing HumanEval dataset pinned to a specific commit.
- **Limitations**: `branch_coverage_potential` is a static metric and may not reflect dynamic testability; `pass_rate` is used only as a filter for functional correctness, not as a primary testability metric. Halstead metrics may be sensitive to LLM-generated redundancy and lack human-grounded baselines.

## Unresolved Panel Concerns (Resolved in this revision)

- **Statistical Testing**: FR-004 and US2 now mandate **only** Wilcoxon Signed-Rank (paired) to align with the paired nature of HumanEval tasks, removing the conflicting Mann-Whitney U (independent) option.
- **Coverage Metrics**: FR-005 clarifies that the [deferred] filter applies to `pass_rate` (execution) to ensure functional correctness, while `branch_coverage_potential` remains a static metric in the Data Model.
- **Data Model Consistency**: The Data Model now consistently uses `branch_coverage_potential` for static analysis, distinguishing it from execution-based coverage.
- **Power Analysis**: FR-008 now explicitly mandates Sensitivity Analysis (MDES) for fixed N=164, replacing A Priori, with SC-005 defining the measurable outcome.
- **Model Feasibility**: FR-009 specifies a quantized 3B model to ensure CPU feasibility, with the GPU fallback noted as non-deterministic.
- **Reproducibility**: FR-001 explicitly mandates pinning to a specific commit hash.
- **Orphaned Requirements**: US1 and US3 have been updated to explicitly anchor FR-005, FR-010, and FR-011.
- **Validation Target Independence**: Limitations and FR-005 clarify that `pass_rate` is a filter, not a testability metric, addressing the circular validation concern.
- **Sample Size Justification**: FR-008 includes justification for MDES calculation to validate the N=164 sample size.
- **Terminology**: All User Stories now consistently distinguish between 'Primary Model' (Salesforce/codegen) and 'Sensitivity Model' (CodeLlama).