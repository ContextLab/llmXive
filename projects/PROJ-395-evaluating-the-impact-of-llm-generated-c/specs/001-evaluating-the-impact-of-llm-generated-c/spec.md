# Feature Specification: Evaluating the Impact of LLM-Generated Code on Memory Usage

**Feature Branch**: `001-eval-llm-memory-impact`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Evaluate whether LLM-generated code exhibits systematically different memory consumption patterns compared to human-written equivalents on standardized algorithmic benchmarks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Profile Memory Usage for Code Solutions (Priority: P1)

The researcher can generate LLM code solutions for algorithmic tasks from a benchmark dataset and profile their memory consumption using Python's `memory_profiler` and `tracemalloc` modules, then compare these measurements against human-written reference solutions.

**Why this priority**: This is the core data collection capability. Without memory measurements for both LLM-generated and human-written code, no comparative analysis is possible. This forms the foundation for all downstream statistical analysis and conclusions.

**Independent Test**: Can be fully tested by running the profiling harness on a representative set of benchmark problems and producing a CSV file with peak and steady-state memory measurements for both LLM and human solutions.

**Acceptance Scenarios**:

1. **Given** a benchmark dataset (HumanEval OR MBPP) is selected, **When** the profiling harness executes an LLM-generated solution on test inputs, **Then** peak memory usage and steady-state memory usage are recorded in bytes and logged to the output file
2. **Given** a benchmark dataset is selected, **When** the profiling harness executes the corresponding human-written reference solution on identical test inputs, **Then** peak memory usage and steady-state memory usage are recorded in bytes and logged to the output file with the same problem identifier
3. **Given** a code solution completes execution, **When** the memory profiling measurement (tracemalloc collection) is taken, **Then** the recorded value does not exceed 7 GB (CI memory limit) and the measurement completes within 30 seconds

---

### User Story 2 - Perform Statistical Analysis on Memory Differences (Priority: P2)

The researcher can run statistical tests on the collected memory measurements to determine whether LLM-generated code exhibits systematically different memory consumption patterns than human-written code, with appropriate corrections for multiple comparisons and handling of execution failures.

**Why this priority**: Statistical analysis transforms raw measurements into evidence. This capability enables the research question to be answered with quantifiable confidence levels, making the findings scientifically valid.

**Independent Test**: Can be fully tested by providing a CSV file of paired memory measurements (including failure penalties) and receiving a statistical report containing p-values, effect sizes, and confidence intervals.

**Acceptance Scenarios**:

1. **Given** N_attempted paired attempts (target N=30), **When** the symmetry check is performed on the difference distribution, **Then** the system reports the result; if symmetry is violated, it automatically switches to a Bootstrap test (iterations)
2. **Given** ≥3 hypothesis tests are performed (e.g., peak memory, steady-state, composite cost), **When** multiple-comparison correction is applied, **Then** a family-wise error rate correction method (e.g., Bonferroni or Holm-Bonferroni) adjusts the significance threshold and reports both raw and corrected p-values
3. **Given** the analysis completes, **When** the statistical report is generated, **Then** the effect size (Cohen's d or rank-biserial correlation) is calculated for each significant finding and reported alongside the p-value

---

### User Story 3 - Analyze Code Feature Correlations with Memory Usage (Priority: P3)

The researcher can extract static code features (lines of code, control flow complexity, library imports) from both LLM-generated and human-written solutions and analyze their correlation with **normalized** memory consumption patterns.

**Why this priority**: This provides mechanistic insight into why memory differences may exist. Understanding which code features drive memory usage enables better prompting strategies and resource-aware code generation pipelines.

**Independent Test**: Can be tested by providing code solutions with extracted features and receiving a regression analysis output showing feature coefficients and their statistical significance against normalized memory.

**Acceptance Scenarios**:

1. **Given** a code solution in Python, **When** static analysis is performed, **Then** at least 3 code features are extracted: lines of code (integer), cyclomatic complexity (integer), and number of library imports (integer)
2. **Given** ≥30 code solutions with extracted features and memory measurements, **When** regression analysis is executed, **Then** a model is fitted using **residual memory** (memory normalized by lines of code) as the dependent variable, and coefficient estimates with standard errors are reported for each predictor
3. **Given** two predictors are potentially collinear (e.g., lines of code and loop depth), **When** collinearity diagnostics are run, **Then** variance inflation factors (VIF) are calculated and any VIF > 5 is flagged in the output report

---

### Edge Cases

- What happens when an LLM-generated solution contains syntax errors preventing execution? → The harness catches the exception, records memory as "timeout" with error type, assigns the maximum resource cost penalty, and continues to the next problem
- How does the system handle benchmark problems with no human-written reference solution available? → Those problems are skipped, and the count of usable pairs is logged
- What happens when memory profiling exceeds the CI memory limit (7 GB)? → The execution is terminated, memory is recorded as "exceeded_limit", and the problem is flagged for manual review
- How does the system handle non-deterministic memory measurements (e.g., due to garbage collection timing)? → Each solution is run multiple times and the median peak memory is recorded to reduce measurement noise.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download HumanEval or MBPP benchmark dataset from HuggingFace Datasets without requiring authentication (See US-1)
- **FR-002**: System MUST generate LLM code solutions using a CPU-tractable model (e.g., CodeLlama, StarCoder, or Phi-2) via HuggingFace Transformers. The system MUST use -bit quantization (`load_in_8bit=True`) if available to reduce memory footprint. Generation MUST complete within 15 minutes per sample. If the primary model exceeds this limit, the system MUST automatically fall back to a smaller model (e.g., Phi) to attempt to maintain the -hour total budget (See US-1)
- **FR-003**: System MUST profile peak and steady-state memory usage using Python's `memory_profiler` and `tracemalloc` modules. Steady-state is defined as the median memory usage over the final portion of execution steps. Each solution is run multiple times, and the median peak memory is recorded. (See US-1)
- **FR-004**: System MUST apply Tobit regression (or Kaplan-Meier estimator) to handle censored data (failures/timeouts) for the primary statistical test. If these methods are unavailable, the system MUST exclude failures and perform a Wilcoxon signed-rank test on the uncensored subset with α = 0.05. Zero-differences MUST be excluded. Ties MUST be handled by assigning average ranks (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) when ≥3 hypothesis tests are performed, reporting both raw and corrected p-values (See US-2)
- **FR-006**: System MUST extract at least 3 static code features: lines of code (integer), cyclomatic complexity (integer), and number of library imports (integer). Additionally, the system MUST calculate 'memory per line of code' (peak_memory_bytes / lines_of_code) as a normalized efficiency metric (See US-3)
- **FR-007**: System MUST calculate variance inflation factors (VIF) for all predictors in regression analysis and flag any VIF > 5 (See US-3)
- **FR-008**: System MUST record all memory measurements in bytes and store results in CSV format with problem identifier, source type (LLM/human), and peak/steady-state values (See US-1)
- **FR-009**: System MUST complete full analysis (data collection + statistics) for N=50 pairs within 6 hours on GitHub Actions free-tier runner (See Assumptions)
- **FR-010**: System MUST handle syntax errors in generated code by recording "N/A" with error type and continuing to next problem (See Edge Cases)

### Key Entities

- **CodeSolution**: A code artifact with attributes: problem_id, source_type (LLM/human), code_text, execution_status, peak_memory_bytes, steady_state_memory_bytes
- **CodeFeature**: Static analysis attributes for a CodeSolution: lines_of_code (integer), cyclomatic_complexity (integer), library_import_count (integer), memory_per_loc (float)
- **MemoryMeasurement**: A paired record with problem_id, llm_peak_memory, human_peak_memory, paired_difference, execution_timestamp
- **StatisticalResult**: Analysis output with test_name, p_value_raw, p_value_corrected, effect_size, confidence_interval, sample_size
- **ResourceCost**: A derived metric combining memory and time, including failure penalties, used for the primary statistical test

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total Resource Cost difference (LLM minus human) is measured against the paired distribution across all N_attempted problems (See US-2)
- **SC-002**: Statistical significance is measured against α = 0.05 threshold with multiple-comparison correction applied (See US-2)
- **SC-003**: Code feature predictive power is measured against the regression model's R-squared and individual coefficient p-values for **normalized memory** (See US-3)
- **SC-004**: Effect size magnitude is measured against Cohen's d benchmarks (small, medium, and large). (See US-2)
- **SC-005**: The system MUST collect and process at least 50 valid paired observations to ensure statistical power (See Assumptions)
- **SC-006**: Collinearity risk is measured against VIF > 5 threshold for any predictor pair (See US-3)
- **SC-007**: The difference in execution failure rates between LLM and human solutions is measured against a tolerance threshold. (See FR-012)
- **SC-008**: The correlation of code features with **residual memory** (memory per LOC) is measured against the regression coefficient significance (See US-3)
- **SC-009**: The impact of failures on the Total Resource Cost is measured against the contribution of the failure penalty term to the composite score (See FR-011)

## Assumptions

- **A-001**: HumanEval or MBPP benchmark datasets contain sufficient paired code solutions (≥30 problems with both LLM and human solutions) for statistical power; if fewer are available, N = [30, N_available] will be recorded and power limitations acknowledged
- **A-002**: Memory profiling using `memory_profiler` and `tracemalloc` provides valid measurements for comparing code memory footprints (validated method in Python ecosystem)
- **A-003**: LLM inference will use CodeLlama-7B, StarCoder, or Phi-2 in CPU-only mode with 8-bit quantization enabled if available to satisfy compute constraints
- **A-004**: Benchmark test inputs are deterministic and produce reproducible memory measurements across runs (verified via multiple-run median).
- **A-005**: The analysis frames findings as ASSOCIATIONAL (observational study, no random assignment); no causal claims about LLM generation causing memory differences will be made
- **A-006**: Dataset-variable fit is satisfied: HumanEval/MBPP provides code solutions and test inputs; code features will be extracted via static analysis (no additional variables needed from dataset)
- **A-007**: Memory measurements will be capped at a predefined CI limit; any execution exceeding this will be flagged and excluded from analysis
- **A-008**: If the idea does not specify a decision threshold for "significant memory difference", a community-standard α = 0.05 with effect size d > 0.5 will be used; sensitivity analysis will sweep α over a range of small values and report how significance rates vary (Justification: essential for robustness against arbitrary threshold selection)
- **A-009**: HumanEval/MBPP contains human-written reference solutions; LLM solutions MUST be freshly generated for all problems using the specified CPU-tractable models (e.g., CodeLlama-7B, StarCoder, or Phi-2) to ensure a fair comparison of generation artifacts. A fixed time budget is essential for CI feasibility (See US-1)
- **A-010**: Execution failures (syntax errors, timeouts, OOM) are treated as right-censored data at a predefined threshold for the primary Tobit regression analysis. If Tobit is unavailable, failures are excluded from the Wilcoxon test. (See US-1)
- **A-011**: The acceptable runtime budget per code execution is a predefined temporal threshold. If a solution exceeds 60 seconds, it is terminated, recorded as 'timeout', and treated as execution failure (memory = 7.001 GB) for statistical ranking purposes, consistent with the handling of syntax errors. (See US-1)
- **A-012**: To mitigate CPU variance (swapping, GC), the system MUST run each solution multiple times and calculate the coefficient of variation (CV) of the peak memory. If CV > 0.1, the measurement is flagged as 'unstable' and the sample is re-run up to 2 additional times. If CV remains > 0.1, the sample is excluded from analysis. (See US-1)