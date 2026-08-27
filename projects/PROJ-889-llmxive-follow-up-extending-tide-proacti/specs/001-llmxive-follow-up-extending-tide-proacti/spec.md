# Feature Specification: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-28  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending TIDE to determine intrinsic properties of hidden code problems that dictate static vs. generative detection boundaries."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

The system MUST ingest the TIDE evaluation dataset and a synthetic dataset. where dependency depth, semantic scope, and syntactic complexity are systematically varied. It MUST parse every code instance to extract quantitative structural features (AST depth, import counts, cyclomatic complexity) to serve as the independent variables for the study.

**Why this priority**: Without a structured, feature-rich dataset, no statistical analysis of the "boundary conditions" can occur. This is the foundational data layer required for all subsequent analysis.

**Independent Test**: A script can be run to load the raw code files, output a CSV containing a substantial number of rows, comprising a mixture of real and synthetic data with columns for `dependency_depth`, `semantic_scope`, `syntactic_complexity`, `ast_depth`, and `ground_truth_label`. The test passes if the CSV is generated without errors and contains the expected number of rows.

**Acceptance Scenarios**:
1. **Given** the TIDE dataset and the synthetic generation script are available, **When** the ingestion pipeline runs, **Then** a unified feature matrix is produced with 700 entries and all structural metrics calculated.
2. **Given** a code instance with a known ground-truth hidden problem, **When** the parser processes it, **Then** the `ground_truth_label` is correctly mapped to the record, and structural metrics are non-null.

---

### User Story 2 - Dual-Pipeline Execution and Latency Logging (Priority: P2)

The system MUST execute two distinct detection pipelines on the unified dataset: a deterministic "TIDE-Lite" static heuristic engine and a generative "TIDE-Original" engine (using a CPU-tractable quantized model). For every instance, the system MUST record the detection outcome (True/False Positive) and the execution latency.

**Why this priority**: This generates the dependent variables (detection success, latency) required to compare the efficacy of static vs. generative methods. It is the core experimental run.

**Independent Test**: The system can be run on a subset of 50 instances. The test passes if the output log contains a sufficient number of entries for both static and generative components. with valid boolean outcomes and positive latency values in milliseconds.

**Acceptance Scenarios**:
1. **Given** the feature matrix from User Story 1, **When** the dual-pipeline runner executes, **Then** every instance is processed by both the static and generative engines, and results are logged with timestamps.
2. **Given** an instance with high syntactic complexity, **When** the static engine runs, **Then** the execution time is recorded and the outcome (Pass/Fail) is logged against the ground truth.

---

### User Story 3 - Boundary Analysis and Statistical Validation (Priority: P3)

The system MUST perform logistic regression to model the probability of static detection success as a function of intrinsic properties. It MUST also conduct stratified McNemar's tests to validate if the performance difference between static and generative methods is statistically significant across complexity bins (low, medium, high).

**Why this priority**: This fulfills the research question by identifying the specific "complexity threshold" and providing statistical rigor to the findings.

**Independent Test**: The analysis script can be run on the logged results. The test passes if it outputs a logistic regression model summary (coefficients, p-values) and a table of McNemar's test results for each complexity bin.

**Acceptance Scenarios**:
1. **Given** the execution logs from User Story 2, **When** the boundary analysis runs, **Then** a logistic regression model is fitted, and the probability of static detection dropping below 0.5 is identified relative to specific feature values.
2. **Given** the detection outcomes for low, medium, and high complexity bins, **When** McNemar's test is applied, **Then** a p-value is returned for each bin indicating statistical significance.

---

### Edge Cases

- **What happens when** the synthetic generation script produces an instance with a dependency depth > 5 or a context scope that exceeds the LLM's context window?
  - *Handling*: The system MUST cap the complexity at the maximum feasible limit for the CPU-only environment and log a warning, ensuring the dataset remains tractable for the 6-hour CI limit.
- **How does system handle** a code instance where the static heuristic and generative model both fail to detect the ground-truth problem?
  - *Handling*: This is recorded as a False Negative for both; the statistical analysis MUST account for these shared failures in the McNemar's test contingency table.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse code instances to extract quantitative features (AST depth, import counts, cyclomatic complexity) and map them to ground-truth labels. (See US-1)
- **FR-002**: System MUST execute a deterministic static heuristic pipeline ("TIDE-Lite") on every dataset instance and record binary detection outcomes. (See US-2)
- **FR-003**: System MUST execute a generative reasoning pipeline (using a CPU-quantized small language model) on every dataset instance and record binary detection outcomes. (See US-2)
- **FR-004**: System MUST log execution latency in milliseconds for every instance processed by both pipelines to enable efficiency analysis. (See US-2)
- **FR-005**: System MUST perform logistic regression to model the probability of static detection success as a function of intrinsic properties and identify the 0.5 probability threshold. (See US-3)
- **FR-006**: System MUST conduct stratified McNemar's tests to determine if the difference in recall between static and generative methods is statistically significant within low, medium, and high complexity bins. (See US-3)
- **FR-007**: System MUST implement a sensitivity analysis that sweeps the complexity threshold definition over a range of values (e.g., {0.01, 0.05, 0.1}) to verify the stability of the identified boundary. (See US-3)
- **FR-008**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) to the p-values generated from the stratified McNemar's tests to control family-wise error rate. (See US-3)

### Key Entities

- **CodeInstance**: Represents a single unit of code (real or synthetic) containing source text, ground-truth label, and extracted structural features.
- **DetectionResult**: Represents the outcome of a pipeline run on a CodeInstance, containing the method type (static/generative), binary outcome, and latency.
- **ComplexityBin**: A categorical grouping (Low, Medium, High) derived from the intrinsic properties of CodeInstances for stratified analysis.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The probability of static detection success is measured against the logistic regression model coefficients to identify the specific feature value where probability drops below 0.5. (See FR-005)
- **SC-002**: The statistical significance of the performance difference between static and generative methods is measured against the McNemar's test p-values, corrected for multiple comparisons. (See FR-006, FR-008)
- **SC-003**: The stability of the identified complexity threshold is measured against the variance in false-positive/false-negative rates across the sensitivity analysis sweep. (See FR-007)
- **SC-004**: The execution efficiency is measured against the total wall-clock time and CPU utilization logs to ensure the analysis completes within the CI time limit. (See FR-004)
- **SC-005**: The dataset coverage is measured against the requirement to include a sufficient number of real instances and 200 synthetic instances with systematically varied properties. (See FR-001)

## Assumptions

- The TIDE evaluation dataset (a representative set of instances) and the synthetic generation script are available and accessible within the CI environment.
- The "TIDE-Original" generative baseline can be approximated by a quantized small language model (e.g., a parameter count in the billions using 4-bit or 8-bit quantization) that fits within a reasonable RAM footprint and runs on CPU-only hardware without requiring CUDA.
- The ground-truth labels provided in the TIDE dataset are independent human annotations and do not derive from the static analysis rules or LLM prompts used in this study.
- The synthetic generation script can reliably vary dependency depth (shallow to deep levels), semantic context scope (local vs. cross-module), and syntactic complexity without generating invalid code that crashes the parser.
- The logistic regression model will converge given the sample size (700 instances); if not, the analysis will default to descriptive statistics with a note on power limitations.
- The "complexity threshold" is defined as the point where the static heuristic's recall drops below [deferred], based on the community-standard expectation that a method is no longer "efficacious" below this recall rate.
- No GPU accelerators are available; all model inference and statistical computations must be performed using CPU-only libraries (e.g., scikit-learn, PyTorch CPU build).
- The multiple-comparison correction method (Bonferroni or Holm) is sufficient for the number of hypothesis tests performed (3 bins).
