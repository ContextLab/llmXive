# Feature Specification: Evaluating the Impact of LLM-Generated Code on Code Coverage

**Feature Branch**: `[001-evaluating-llm-code-coverage]`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description:  
> *How does code coverage differ between LLM-generated code and human-written code for equivalent programming tasks, and which code structures or problem types exhibit the largest coverage gaps?*  

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated LLM‑code generation & coverage measurement (Priority: P1)

A researcher wants to run a reproducible pipeline that (a) generates one Python solution per programming task using an LLM, (b) executes the supplied test suite, and (c) records line‑ and branch‑coverage metrics.

**Why this priority**: This is the core data‑collection step; without it no analysis is possible.

**Independent Test**: Execute the pipeline on a random sample of tasks from MBPP and verify that for each task a JSON record containing the generated source code, test‑run outcome, and `line_coverage` & `branch_coverage` percentages is produced.

**Acceptance Scenarios**:

1. **Given** the MBPP task list and a valid LLM API key, **when** the pipeline is invoked, **then** exactly one Python file is generated per task and stored in `generated/`.
2. **Given** a generated file and its associated test suite, **when** `pytest --cov` is run, **then** a coverage report is written to `coverage_reports/` containing both line‑ and branch‑coverage percentages.

---

### User Story 2 – Comparative statistical analysis (Priority: P2)

A researcher wants to compare the coverage of LLM‑generated solutions against a human‑written baseline and determine whether any observed differences are statistically significant.

**Why this priority**: Provides the primary empirical answer to the research question.

**Independent Test**: Run the analysis on a paired set of tasks (LLM vs. human) and confirm that a statistical summary table is produced containing mean differences, paired‑t test p‑value, and Cohen’s d effect size.

**Acceptance Scenarios**:

1. **Given** coverage tables for LLM and human solutions on the same 100 tasks, **when** the analysis script is executed, **then** it outputs a CSV `stats_summary.csv` with columns: `mean_llm`, `mean_human`, `mean_diff`, `p_value`, `cohen_d`.
2. **Given** the same inputs, **when** the p‑value is ≤ 0.05, **then** the script flags the result as “significant” in the summary.

---

### User Story 3 – Stratified insight & visualization (Priority: P3)

A researcher wants to see how coverage gaps vary by problem difficulty and by code pattern (loops, conditionals, recursion) and to export visualizations for reporting.

**Why this priority**: Enables the “which structures exhibit the largest gaps?” part of the question and supports downstream communication.

**Independent Test**: After the statistical analysis, request a stratified report for the “loops” pattern; verify that a box‑plot PNG `coverage_by_pattern_loops.png` is generated and that the accompanying CSV contains per‑task coverage differences for that pattern.

**Acceptance Scenarios**:

1. **Given** the full coverage dataset with annotated problem metadata, **when** the stratification script is run with `--pattern loops`, **then** a CSV `stratified_loops.csv` and a PNG `coverage_by_pattern_loops.png` appear in `outputs/`.
2. **Given** the same run, **when** the mean branch‑coverage gap for the “hard” difficulty tier is computed, **then** the value is reported in `stratified_summary.csv`.

---

### Edge Cases

- **Compilation/Runtime Failure**: If a generated script raises a `SyntaxError` or crashes during test execution, the pipeline must record the failure, skip coverage calculation for that task, and continue without aborting the whole run.  
- **Missing Test Suite**: If a task in MBPP lacks a test file, the pipeline should log a warning and exclude the task from the paired analysis.  
- **API Rate‑Limit Exhaustion**: When the LLM service returns a rate‑limit error, the pipeline must back‑off (wait 60 seconds) and retry up to 3 times before marking the task as “generation failed”.  

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest the full MBPP and HumanEval task lists and expose them as a normalized JSON catalog. *(See US-1)*
- **FR-002**: The system MUST generate exactly one Python solution per task by invoking a configurable LLM endpoint (e.g., OpenAI GPT‑4 or CodeLlama‑7B). *(See US-1)*
- **FR-003**: The system MUST execute each generated solution against its official test suite using `pytest --cov` and record both line‑ and branch‑coverage percentages. *(See US-1)*
- **FR-004**: The system MUST store paired coverage records (LLM vs. human) in a CSV `coverage_pairs.csv` for downstream statistical testing. *(See US-2)*
- **FR-005**: The system MUST perform a paired‑t test (α = 0.05) on the coverage differences and output `stats_summary.csv` with mean difference, p‑value, and Cohen’s d. *(See US-2)*
- **FR-006**: The system MUST apply a family‑wise error correction (Bonferroni) when multiple subgroup tests are performed. *(Methodological soundness – multiplicity)*
- **FR-007**: The system MUST allow stratification by at least three metadata dimensions: problem difficulty, code pattern, and presence of boundary‑case tests. *(See US-3)*
- **FR-008**: The system MUST generate visualizations (box‑plots, bar‑charts) using only matplotlib/seaborn and save them as PNG files. *(See US-3)*
- **FR-009**: The system MUST validate that each dataset entry includes the required variables: `task_id`, `prompt`, `human_solution`, `test_suite`. *(Dataset‑variable fit)*
- **FR-010**: The system MUST treat coverage differences as **associational** findings, not causal claims, and must label all result statements accordingly. *(Inference framing)*
- **FR-011**: The system MUST report coverage‑difference sensitivity across three absolute‑diff thresholds {0.01, 0.05, 0.10} and include the resulting variation in `sensitivity_report.csv`. *(Threshold justification & sensitivity)*
- **FR-012**: The system MUST use `pytest‑cov` (v4.0 or later) as the validated coverage measurement tool. *(Measurement validity)*
- **FR-013**: The system MUST log collinearity diagnostics (Variance Inflation Factor) for any numeric predictors derived from code‑pattern counts before reporting effect sizes. *(Predictor collinearity)*

*Clarification needed*:

- **FR-002**: [NEEDS CLARIFICATION: Which LLM endpoint (OpenAI GPT‑4 vs. CodeLlama‑7B) will be the default for the free‑CPU CI environment?]  
- **FR-009**: [NEEDS CLARIFICATION: Do the HumanEval entries include explicit branch‑coverage expectations, or must we rely solely on measured coverage?]  
- **FR-011**: [NEEDS CLARIFICATION: Should the sensitivity analysis also sweep the significance α (e.g., 0.01, 0.05, 0.10) or only the coverage‑diff thresholds?]

### Key Entities *(include if feature involves data)*

- **TaskCatalog**: Represents a programming task; attributes: `task_id`, `prompt`, `human_solution`, `test_suite_path`, `difficulty`, `code_patterns` (list).  
- **GeneratedSolution**: Holds the LLM‑produced source code, generation timestamp, and any generation metadata (model used, temperature).  
- **CoverageRecord**: Contains `task_id`, `line_coverage`, `branch_coverage`, `run_status` (success/failure).  

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The pipeline processes **≥ 100 distinct tasks** (including both MBPP and HumanEval) and produces a complete `coverage_pairs.csv` without manual intervention. *(See US-1)*
- **SC-002**: The paired‑t test yields a **p‑value ≤ 0.05** for the overall mean branch‑coverage difference *or* correctly reports non‑significance, and the effect size (Cohen’s d) is calculated for every analysis run. *(See US-2)*
- **SC-003**: The sensitivity analysis across thresholds {0.01, 0.05, 0.10} shows that the sign of the mean coverage gap does **not** flip; the variation is documented in `sensitivity_report.csv`. *(See FR-011)*
- **SC-004**: All generated visualizations are viewable PNG files with a resolution of at least **800 × 600 px** and include axis labels and legends. *(See US-3)*
- **SC-005**: No single CI job exceeds **6 hours** wall‑clock time, **≤ 2 CPU cores**, **≤ 7 GB RAM**, and **≤ 14 GB disk** usage on the GitHub Actions free tier. *(Compute feasibility)*

---

## Assumptions

- The CI environment provides Python 3.10+, `pip`, and internet access for dataset download and LLM API calls.  
- The MBPP and HumanEval datasets together contain **≤ 1 GB** of source files, comfortably fitting the 7 GB RAM limit after loading.  
- The chosen LLM (either GPT‑4 via OpenAI or CodeLlama‑7B via HuggingFace) can be invoked with **CPU‑only** inference; if the default model exceeds CPU limits, the pipeline will fall back to a smaller open‑source model (e.g., `bigcode/starcoderbase-3b`).  
- All test suites are deterministic and complete within **30 seconds** per task on the free‑CPU runner.  
- Researchers will supply a valid API key for the selected LLM service via the `LLM_API_KEY` secret; the pipeline will respect rate limits by exponential back‑off.  
- Coverage is measured **associationally**; no causal language will be used in the final report.  
- The statistical analysis assumes **paired independence** of tasks and normality of coverage differences; if normality fails, a Wilcoxon signed‑rank test will be used (fallback documented).  

---
