# Feature Specification: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

**Feature Branch**: `001-logical-dependency-icl`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Many-Shot CoT-ICL: Making In-Context Learning Truly Learn"

## User Scenarios & Testing

### User Story 1 - Logical Dependency Graph Construction (US-001) (Priority: P1)

**Journey**: A researcher needs to transform raw Chain-of-Thought (CoT) demonstration traces from the geometry and number theory datasets into structured Directed Acyclic Graphs (DAGs) representing logical dependency chains. This is the foundational step to derive the "Logical Difficulty Score" required for the primary hypothesis test.

**Why this priority**: Without accurate logical parsing and DAG construction, the "Logical Ascending" ordering strategy cannot be generated. This is the core innovation distinguishing this study from the baseline semantic curvature approach.

**Independent Test**: The system can ingest a raw CoT trace file, output a valid DAG structure for each example, and calculate a maximum path depth score that correlates with human-judged logical complexity from a pre-existing labeled subset of 50 geometry problems from the GeoQA dataset (rated by 3 expert mathematicians, Cohen's κ ≥ 0.75), verified against this labeled subset.

**Acceptance Scenarios**:

1. **Given** a raw CoT demonstration file containing geometry problems, **When** the parser processes a trace with a multi-step derivation, **Then** the system outputs a DAG where nodes represent atomic logical steps and edges represent explicit dependency relationships, and the resulting dataset exhibits a standard deviation of maximum path depth ≥ 1.5 across the 64-shot sample.
2. **Given** a trace with circular or self-referential logic (invalid for DAGs), **When** the parser processes it, **Then** the system flags the example as "invalid" and excludes it from the training set if it detects a cycle of length ≤ 5 steps or if a node has > 3 incoming edges from steps occurring > 10 lines prior, logging the specific step causing the cycle.
3. **Given** a dataset of 1000 CoT traces, **When** the parser runs, **Then** it completes the DAG construction for all valid traces within 15 minutes on a 2-core CPU runner, outputting a JSON manifest of dependency depths.

---

### User Story 2 - Prompt Ordering Strategy Generation (US-002) (Priority: P2)

**Journey**: A researcher needs to generate three distinct multi-shot prompt configurations for each test run: (a) Original CDS (semantic curvature), (b) Logical Ascending (sorted by DAG depth), and (c) Logical Random (shuffled). This enables the comparative analysis of ordering strategies.

**Why this priority**: This step operationalizes the independent variable (ordering strategy) to test the research question. It must be reproducible and deterministic (given the same seed) to ensure valid statistical comparison.

**Independent Test**: The system can take the parsed dataset and the three strategy definitions, generating three distinct prompt files where the sequence of examples strictly adheres to the specified sorting or shuffling logic.

**Acceptance Scenarios**:

1. **Given** a set of 64 parsed examples with calculated "Logical Difficulty Scores", **When** the "Logical Ascending" strategy is applied, **Then** the resulting prompt file orders examples strictly from lowest to highest dependency depth (non-decreasing sequence).
2. **Given** the same set of 64 examples, **When** the "Logical Random" strategy is applied with a fixed seed, **Then** the resulting prompt file contains the same examples in a different order than the "Logical Ascending" version, but maintains the same distribution of difficulty scores.
3. **Given** a request to generate prompts for 10 random seeds, **When** the system executes, **Then** it produces multiple distinct prompt files (3 strategies × 10 seeds) without duplication of the exact same ordering within a strategy group.

---

### User Story 3 - CPU-Only Inference & Statistical Analysis (US-003) (Priority: P3)

**Journey**: A researcher needs to execute inference on the generated prompts using two model classes (Reasoning vs. Non-Reasoning) on a CPU-only environment, then perform a two-way ANOVA on the mean accuracy per seed to test for interaction effects between model type and ordering strategy.

**Why this priority**: This delivers the final empirical evidence. The analysis must be robust enough to run within the 6-hour free-tier limit while maintaining statistical validity (controlling for multiplicity and power).

**Independent Test**: The system can run inference on a sample of 64-shot prompts using `llama.cpp` (CPU mode), collect accuracy metrics, aggregate them by seed, and output a statistical report confirming whether the interaction term in the ANOVA (performed on mean accuracy per seed) is significant (p < 0.05) or not.

**Acceptance Scenarios**:

1. **Given** a set of 30 generated prompts and a CPU-compatible model (e.g., Qwen3-14B quantized to Q4_K_M), **When** the inference runner executes on an x86_64 runner with ≥ 16 GB RAM, **Then** it completes all 30 runs within 4 hours, recording accuracy and variance for each seed.
2. **Given** the collected accuracy data aggregated by seed, **When** the statistical analysis module runs, **Then** it performs a two-way ANOVA on the mean accuracy per seed and outputs a p-value for the interaction term, along with post-hoc Tukey test results for pairwise comparisons.
3. **Given** the presence of multiple hypothesis tests (comparing 3 strategies across 2 models), **When** the analysis runs, **Then** it applies a Bonferroni correction (or equivalent) to adjust the significance threshold, ensuring the family-wise error rate is controlled.

---

### Edge Cases

- **What happens when** a CoT trace contains ambiguous logical steps that cannot be uniquely mapped to a DAG node?
  - *System handles*: The parser defaults to a "sequential chain" assumption (linear dependency) and flags the example for manual review in the log, excluding it from the "Logical Ascending" sort if the ambiguity exceeds a substantial threshold of the total steps.
- **How does the system handle** a model crashing or timing out during inference on a specific prompt?
  - *System handles*: The runner retries the specific prompt up to 2 times with a 30-second backoff. If it fails again, the trial is marked as "failed," excluded from the accuracy calculation for that seed/strategy, and the total sample size is adjusted in the statistical report.
- **What happens when** the dataset lacks sufficient variance in logical depth (e.g., all examples have depth 1)?
  - *System handles*: The system detects zero variance in the "Logical Difficulty Score" distribution and halts the run, reporting a "Data Insufficiency" error, as the "Logical Ascending" strategy would be indistinguishable from a random shuffle.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse CoT traces into Directed Acyclic Graphs (DAGs) to calculate a "Logical Difficulty Score" based on maximum path depth, AND this score MUST correlate (Pearson r ≥ 0.6) with external GeoQA difficulty ratings before the dataset is used, serving the User Story 1 data preparation (See US-001).
- **FR-002**: System MUST generate three distinct prompt orderings with a moderate number of shots (Original CDS, Logical Ascending, Logical Random) for every test seed, serving the User Story 2 experimental design (See US-002).
- **FR-003**: System MUST execute inference using `llama.cpp` in CPU-only mode (no CUDA/GPU) for both reasoning and non-reasoning model classes, serving the User Story 3 compute constraint (See US-003).
- **FR-004**: System MUST perform a two-way ANOVA on the mean accuracy per seed (aggregated from individual runs) to test the interaction between "Model Type" and "Ordering Strategy", serving the User Story 3 statistical analysis (See US-003).
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the post-hoc test results to control the family-wise error rate, serving the methodological soundness requirement for multiplicity (See US-003).
- **FR-006**: System MUST validate that the test set used for accuracy measurement is distinct from the training set used to construct the logical DAGs, serving the methodological soundness requirement for independence (See US-001).
- **FR-007**: System MUST validate the parser against a gold-standard subset ([deferred] of traces manually annotated by experts) to ensure a precision ≥ 0.85 and recall ≥ 0.80 for edge detection before generating the main dataset, serving the methodological soundness requirement for parser reliability (See US-001).

### Key Entities

- **CoT Trace**: A text string containing a problem statement and a step-by-step reasoning path.
- **Logical Difficulty Score**: A scalar integer representing the maximum path depth in the DAG derived from a CoT Trace.
- **Prompt Configuration**: A structured object containing 64 examples ordered by a specific strategy (Ascending, Random, CDS).
- **Inference Result**: A record containing model ID, seed, strategy, accuracy metric, and execution time.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The variance of accuracy across 10 random seeds for the "Logical Ascending" strategy is measured against the variance of the "Logical Random" strategy for non-reasoning models to determine stability improvement (≥ 15% reduction in variance, p < 0.10 via Levene's test) (See US-003).
- **SC-002**: The interaction p-value from the two-way ANOVA (Model Type × Ordering Strategy) is measured against the alpha level of 0.05 (adjusted for multiplicity) to determine if the alignment hypothesis is supported (See US-003).
- **SC-003**: The total execution time for the full inference and analysis pipeline is measured against the 6-hour free-tier runner limit to ensure compute feasibility (See US-003).
- **SC-004**: The proportion of CoT traces successfully parsed into valid DAGs is measured against the total number of traces in the dataset to verify data quality and parser robustness (See US-001).
- **SC-005**: The accuracy difference between "Logical Ascending" and "Original CDS" for non-reasoning models is measured against the accuracy difference for reasoning models to validate the differential effect hypothesis (p-value < 0.05 Bonferroni-adjusted AND partial eta-squared ≥ 0.06) (See US-003).

## Assumptions

- The geometry and number theory datasets from the "Many-Shot In-Context Learning" benchmark are available via HuggingFace and contain sufficient CoT traces with explicit logical steps to construct meaningful DAGs.
- The `llama.cpp` inference server can run the selected models (e.g., Qwen3-14B quantized to Q4_K_M) within the 16 GB RAM limit of the x86_64 runner without requiring GPU acceleration.
- The "Logical Difficulty Score" derived from rule-based parsing (maximum path depth) is a valid proxy for the cognitive load required to process the reasoning trace, as hypothesized in the research question, PROVIDED it correlates (r ≥ 0.6) with external expert ratings.
- The sample size (64 shots × 10 seeds × 2 models × 3 strategies = 360 runs) provides sufficient statistical power to detect a moderate interaction effect, given the constraints of the free-tier runner.
- The "Original CDS" ordering strategy can be approximated using standard embedding-based curvature metrics available in the referenced literature, even if the exact proprietary implementation is not accessible.
- The rule-based parser for logical steps (using `networkx`) is robust enough to handle the syntactic variations in CoT traces, provided it is validated against a gold-standard subset (precision ≥ 0.85, recall ≥ 0.80) as required by FR-007.
- The parser validation against the gold-standard subset ([deferred] of traces) is feasible within the project timeline.