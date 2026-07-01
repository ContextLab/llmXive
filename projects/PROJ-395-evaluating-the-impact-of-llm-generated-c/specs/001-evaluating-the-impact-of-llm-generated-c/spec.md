# Feature Specification: Evaluating the Impact of LLM-Generated Code on Memory Usage

**Feature Branch**: `001-eval-llm-memory-impact`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Evaluate whether LLM-generated code exhibits systematically different memory consumption patterns compared to human-written equivalents on standardized algorithmic benchmarks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate and Profile Memory Usage for Code Solutions (Priority: P1)

The researcher can generate LLM code solutions for algorithmic tasks from a **single selected** benchmark dataset (HumanEval OR MBPP) and profile their memory consumption using Python's memory profiling tools, then compare these measurements against human-written reference solutions.

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
- What happens when memory profiling exceeds the CI memory limit (7 GB)? → The execution is terminated, memory is recorded as "exceeded_limit" with the maximum cost penalty, and the problem is flagged for manual review
- How does the system handle non-deterministic memory measurements (e.g., due to garbage collection timing)? → Each solution is run multiple times and the median peak memory is recorded to reduce measurement noise.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download **exactly one** of HumanEval or MBPP benchmark dataset from HuggingFace Datasets without requiring authentication (See US-1)
- **FR-002**: System MUST generate LLM code solutions using a CPU-tractable model (Phi-3-mini-3.8B or equivalent <4B params via HuggingFace Transformers in CPU mode) with a **generation timeout of 180 seconds**; if generation exceeds this, the problem is skipped (See US-1)
- **FR-003**: System MUST profile peak and steady-state memory usage using Python's `memory_profiler` and `tracemalloc` modules for each code execution (See US-1)
- **FR-004**: System MUST execute a Wilcoxon signed-rank test on paired memory measurements **or a Bootstrap test** if symmetry is violated, with significance threshold α = 0.05 (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) when ≥3 hypothesis tests are performed, reporting both raw and corrected p-values (See US-2)
- **FR-006**: System MUST extract at least 3 static code features: lines of code, cyclomatic complexity, and number of library imports (See US-3)
- **FR-007**: System MUST calculate variance inflation factors (VIF) for all predictors in regression analysis and flag any VIF > 5 (See US-3)
- **FR-008**: System MUST record all memory measurements in bytes and store results in CSV format with problem identifier, source type (LLM/human), and peak/steady-state values (See US-1)
- **FR-009**: System MUST complete full analysis (data collection + statistics) for **N=30 paired problems** within 6 hours on a standard GitHub Actions runner (2 cores, 7GB RAM) (See Assumptions)
- **FR-010**: System MUST handle syntax errors in generated code by recording "timeout" with error type and assigning the maximum resource cost penalty (See Edge Cases)
- **FR-011**: System MUST calculate a **Total Resource Cost** metric defined as `Memory_Bytes * Time_Seconds + (Failure_Penalty * 7GB * 60s)` for each run, treating timeouts as maximum cost (See US-2, Scientific Soundness)
- **FR-012**: System MUST report execution failure rates (syntax errors, runtime exceptions, timeouts) as a distinct metric alongside the statistical results (See US-2)
- **FR-013**: System MUST perform a symmetry check (Shapiro-Wilk or Q-Q plot) on the difference distribution of the Total Resource Cost; if violated, the system MUST default to a Bootstrap test with a sufficient number of iterations for p-value estimation (See US-2)
- **FR-014**: System MUST calculate a **Composite Score** for the primary paired comparison, defined as the Total Resource Cost, to ensure failures are mathematically integrated into the systematic difference analysis (See US-2, Scientific Soundness)

### Key Entities

- **CodeSolution**: A code artifact with attributes: problem_id, source_type (LLM/human), code_text, execution_status, peak_memory_bytes, steady_state_memory_bytes
- **CodeFeature**: Static analysis attributes for a CodeSolution: lines_of_code (integer), cyclomatic_complexity (integer), library_import_count (integer)
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
- **SC-005**: Sample size adequacy is measured against the minimum N = 30 paired attempts required for statistical power; the system reports the achieved N, and the research report validates if N >= 30 (See Assumptions)
- **SC-006**: Collinearity risk is measured against VIF > 5 threshold for any predictor pair (See US-3)
- **SC-007**: The difference in execution failure rates between LLM and human solutions is measured against a tolerance threshold. (See FR-012)
- **SC-008**: The correlation of code features with **residual memory** (memory per LOC) is measured against the regression coefficient significance (See US-3)
- **SC-009**: The impact of failures on the Total Resource Cost is measured against the contribution of the failure penalty term to the composite score (See FR-011)

## Assumptions

- **A-001**: HumanEval or MBPP benchmark datasets contain sufficient paired code solutions (≥30 problems with both LLM and human solutions) for statistical power; if fewer are available, N = [30, N_available] will be recorded and power limitations acknowledged
- **A-002**: Memory profiling using `memory_profiler` and `tracemalloc` provides valid measurements for comparing code memory footprints (validated method in Python ecosystem)
- **A-003**: LLM inference will use Phi-3-mini-3.8B (or equivalent <4B params) in CPU-only mode with default precision (no 8-bit/4-bit quantization, no CUDA) to satisfy compute constraints
- **A-004**: Benchmark test inputs are deterministic and produce reproducible memory measurements across runs (verified via multiple runs).
- **A-005**: The analysis frames findings as ASSOCIATIONAL (observational study, no random assignment); no causal claims about LLM generation causing memory differences will be made
- **A-006**: Dataset-variable fit is satisfied: HumanEval/MBPP provides code solutions and test inputs; code features will be extracted via static analysis (no additional variables needed from dataset)
- **A-007**: Memory measurements will be capped at the CI limit.; any execution exceeding this will be flagged and excluded from analysis, but included in the Total Resource Cost as a penalty
- **A-008**: If the idea does not specify a decision threshold for "significant memory difference", a community-standard α = 0.05 with effect size d > 0.5 will be used; sensitivity analysis will sweep α across a range of small significance thresholds and report how significance rates vary
- **A-009**: HumanEval and MBPP provide the problem definitions and human reference solutions only. The system MUST generate LLM solutions freshly for every problem in the selected benchmark subset. This design ensures a fair comparison where the LLM is evaluated on its ability to synthesize solutions for standard tasks, rather than retrieving pre-computed outputs. (See US-1)
- **A-010**: The analysis MUST include **all** problems where an attempt was made. Execution failures (syntax errors, runtime exceptions, or timeouts) MUST **NOT** be excluded from the statistical paired comparison. Instead, they MUST be assigned a maximum resource cost penalty to reflect the true cost of instability. (See US-2, FR-011, FR-014)
- **A-011**: The system MUST enforce a per-solution execution timeout of 60 seconds. If a code solution exceeds this limit, it MUST be terminated, recorded as 'timeout', and included in the analysis with the maximum resource cost penalty. The total analysis budget of 6 hours accommodates the generation, execution, and profiling of up to 30 problems (approx. 600 seconds per problem including overhead), ensuring the CI limit is respected while allowing sufficient time for LLM inference on CPU (See US-1, FR-009).
- **A-012**: The dataset selection is mutually exclusive: The system MUST select **exactly one** dataset (HumanEval OR MBPP) at the start of execution. Running both is out of scope for the 6-hour budget.
- **A-013**: The symmetry check (FR-013) applies to the difference distribution of the **Total Resource Cost** (including failure penalties), ensuring the statistical test is valid even when failures are present.