# Feature Specification: Evaluating the Effectiveness of Code Simplification on LLM Performance

**Feature Branch**: `[001-eval-code-simplification]`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Assess whether automated code‑simplification (dead‑code removal, boolean reduction) improves pass@1 accuracy and inference latency of a small pre‑trained code model on the HumanEval benchmark."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Benchmark Comparison (Priority: P1)

A researcher wants to run the HumanEval benchmark on a code LLM using **both** the original code snippets **and** their AST‑simplified versions, so they can directly compare model accuracy (pass@1) and inference latency.

**Why this priority**: This is the core scientific question of the project; without a paired comparison the hypothesis cannot be evaluated.

**Independent Test**: Execute the full end‑to‑end pipeline on a representative subset of HumanEval (e.g., a modest number of problems) and verify that two CSV files are produced – one for raw inputs and one for simplified inputs – each containing pass@1 scores and per‑sample latency.

**Acceptance Scenarios**:

1. **Given** the pipeline is configured with the HumanEval dataset and the AST simplifier, **When** the researcher triggers the "run‑benchmark" command, **Then** the system outputs two result tables with matching problem IDs for raw and simplified inputs.  
2. **Given** the result tables exist, **When** the researcher inspects them, **Then** each table includes columns for `problem_id`, `pass@1`, `token_count`, and `inference_time_ms`.

---

### User Story 2 – Metric Logging & Token Accounting (Priority: P2)

A researcher needs precise logs of token counts and wall‑clock inference time for every sample, because these metrics will be used in statistical testing and visualisation.

**Why this priority**: Accurate measurement is required to substantiate any claimed performance gain and to satisfy the multiplicity/power considerations.

**Independent Test**: After a benchmark run, open the generated log file and confirm that for every problem there is a line containing both `token_count` and `inference_time_ms`.

**Acceptance Scenarios**:

1. **Given** a benchmark run has completed, **When** the researcher opens `metrics_raw.csv`, **Then** each row contains non‑negative integer `token_count` and numeric `inference_time_ms` values.

---

### User Story 3 – Statistical Analysis & Visualization (Priority: P3)

A researcher wants a reproducible statistical report (paired Wilcoxon signed‑rank test with FWER correction) and a Matplotlib plot that juxtaposes accuracy and latency improvements across the problem set.

**Why this priority**: The report provides the evidence needed to accept or reject the hypothesis; the plot aids interpretation and communication.

**Independent Test**: Run the "analyze‑results" script; it should produce a PDF report containing the test statistic, p‑value, effect size, and a figure with two side‑by‑side bar charts (raw vs simplified) for accuracy and latency.

**Acceptance Scenarios**:

1. **Given** the two result tables are present, **When** the researcher executes the analysis script, **Then** a file `analysis_report.pdf` is created that includes a statistically significant result statement (or lack thereof) and the required visualizations.

---

### Edge Cases

- **Unparsable Code**: What happens when a HumanEval snippet cannot be parsed by Python's `ast` module?  
- **Semantic Change**: How does the system detect if the simplification unintentionally alters the program's semantics?  
- **Model Failure**: How does the pipeline handle a timeout or crash during inference for a particular sample?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download and load the HumanEval benchmark (code snippets + reference solutions) from HuggingFace Datasets. *(See US-1)*
- **FR-002**: The system MUST apply an AST‑based preprocessing pipeline that (a) removes dead code, and (b) reduces boolean expressions, producing syntactically valid Python code. *(See US-1)*
- **FR-003**: The system MUST execute inference with a 4‑bit quantized StarCoder‑1.3B model via `llama.cpp` on CPU‑only runners, respecting the ≤7 GB RAM limit. *(See US-1)*
- **FR-004**: For each inference call, the system MUST record (i) total token count of the input, and (ii) wall‑clock inference time in milliseconds, and write these to `metrics_raw.csv` and `metrics_simplified.csv`. *(See US-2)*
- **FR-005**: The system MUST perform a paired Wilcoxon signed‑rank test on pass@1 scores and a paired Wilcoxon test on inference times, applying a Bonferroni correction for the two hypotheses (accuracy and latency). *(See US-3)*
- **FR-006**: The system MUST generate a PDF report containing test statistics, Bonferroni‑corrected p‑values, effect sizes (Cohen's d), and Matplotlib visualizations comparing raw vs simplified results. *(See US-3)*
- **FR-007**: If a code snippet fails AST parsing, the system MUST log the failure to `parse_failures.log` with fields: `problem_id`, `error_type`, `timestamp`, and a `stack_trace` snippet. *(See Edge Case: Unparsable Code)*
- **FR-008**: If simplification produces code that raises a syntax error or changes expected output (detected by running the reference test harness), the system MUST write the snippet to `flagged_snippets.csv` with fields: `problem_id`, `error_type`, and `code_diff` (original vs simplified). *(See Edge Case: Semantic Change)*
- **FR-009**: The system MUST enforce a per‑sample inference timeout of 30 seconds; on timeout it logs the event and records `inference_time_ms = 30000` with a failure flag. *(See Edge Case: Model Failure)*
- **FR-010**: The system MUST include a power/sample-size justification in the final report, documenting the minimum detectable effect size for the chosen sample size (≥200 problems) at power ≥0.8. *(See Constitution Principle VII)*

### Key Entities *(include if feature involves data)*

- **HumanEvalProblem**: Represents a single benchmark item; key attributes are `problem_id`, `prompt_code`, `reference_solution`.  
- **SimplifiedProblem**: Derived from `HumanEvalProblem` after AST transformation; retains `problem_id` and includes `simplified_code`.  
- **InferenceResult**: Captures `problem_id`, `pass@1`, `token_count`, `inference_time_ms`, and `status` (success/failure).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pass@1 accuracy difference (simplified minus raw) is measured and compared against a [deferred] effect-size threshold; the paired Wilcoxon test p-value is reported with Bonferroni correction. *(See US-1 & US-3)*
- **SC-002**: Median inference time ratio (simplified/raw) is measured and compared against a [deferred] effect-size threshold; the paired Wilcoxon test p-value is reported with Bonferroni correction. *(See US-2 & US-3)*
- **SC-003**: Token count ratio (simplified/raw) is measured for each problem; the proportion of problems achieving a [deferred] reduction threshold is computed. This is a prerequisite verification—accuracy/latency analysis proceeds only if token reduction is achieved. *(See US-2)*
- **SC-004**: The analysis report PDF must be generated successfully and contain all required statistical tables and figures without manual post‑processing. *(See US-3)*
- **SC-005**: No more than 5% of benchmark items may be dropped due to unparsable code or semantic‑change warnings; otherwise the experiment is considered under‑sampled. *(See Edge Cases)*

## Assumptions

- The HumanEval dataset includes all variables needed for pass@k computation (code prompt, reference solution, and test harness).  
- A StarCoder model quantized to low-bit precision fits within the memory constraints of the free-tier GitHub Actions runner.  
- CPU‑only inference via `llama.cpp` can process the selected subset (≤ 500 problems) within the specified job limit.  
- The Wilcoxon signed‑rank test is appropriate for the paired, non‑normally distributed metric distributions; no alternative parametric test is required.  
- The significance threshold is fixed at α = 0.05, and Bonferroni correction is sufficient for the two primary hypotheses (accuracy, latency).  
- No GPU or CUDA libraries will be used; all code runs on pure Python/CPU libraries compatible with the runner environment.  
- The simplification pipeline is **semantics‑preserving** for the majority of snippets; any detected semantic change is logged but does not invalidate the overall analysis.  
- Power analysis is deferred; the chosen sample size (≈ 200–500 problems) is assumed adequate for detecting medium effect sizes, and the limitation will be noted in the final report (see FR-010).