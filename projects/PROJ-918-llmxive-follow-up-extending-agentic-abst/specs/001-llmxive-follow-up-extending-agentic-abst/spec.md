# Feature Specification: llmXive follow-up: extending "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"

**Feature Branch**: `001-llmxive-abstention-meta-critic`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Agentic Abstention: Do Agents Know When to Stop Instead of Act?'"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

The system must ingest the "Agentic Abstention" benchmark dataset (Environment-based subset) and extract low-level, non-semantic state features (and low-level semantic proxies) from interaction trajectories to create a training-ready dataset for the meta-critic.

**Why this priority**: Without a clean, feature-engineered dataset, no model can be trained. This is the foundational step that defines the "information-theoretic lower bound" inputs (state features vs. full semantic context).

**Independent Test**: The pipeline can be executed to produce a CSV/Parquet file containing a representative set of tasks with extracted features (search count, error frequency, token usage, turn number, query-context embedding distance) and binary labels (abstain/continue), which can be validated for schema correctness and non-circularity.

**Acceptance Scenarios**:

1. **Given** the raw interaction logs from the specified subset, **When** the extraction script runs on the subset, **Then** the output file contains the full set of rows from the specified subset with the specified feature columns and no full semantic context strings.
2. **Given** a task trajectory where the agent successfully completes the task, **When** the feature extractor processes the final turn, **Then** the "cumulative token usage" and "turn number" are correctly recorded as numeric values, and the label is set to "continue" (if not aborted) or "abstain" (if the ground truth indicates it was impossible).
3. **Given** a trajectory with error messages, **When** the extractor runs, **Then** the "error message frequency" count accurately reflects the number of unique error types encountered in the log.

---

### User Story 2 - Meta-Critic Model Training and Evaluation (Priority: P2)

The system must train a lightweight, CPU-optimized gradient-boosted tree classifier (e.g., XGBoost/LightGBM) on the extracted state features to predict the optimal stopping decision, and evaluate its performance against a full-context baseline.

**Why this priority**: This is the core research experiment. It tests the hypothesis that state-based heuristics (and low-level proxies) can compress the stopping logic, directly addressing the efficiency-accuracy trade-off.

**Independent Test**: The training job completes on a CPU-only runner, producing a model file and a performance report showing Timely Abstention Recall, Token Consumption, and Latency metrics compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the feature-engineered dataset, **When** the training script executes on a 2-core CPU instance, **Then** the model converges within the 6-hour time limit and produces a binary classifier without requiring GPU or CUDA resources.
2. **Given** a held-out test set of tasks, **When** the trained meta-critic evaluates the state features, **Then** the "Timely Abstention Recall" is calculated and reported, and it is compared against the full-context CONVOLVE baseline recall.
3. **Given** the simulation loop, **When** the meta-critic triggers an abstention, **Then** the system logs the specific turn number and the feature vector that triggered the decision for auditability.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

The system must perform statistical significance testing (Two-sample Kolmogorov-Smirnov or Mann-Whitney U) on the performance metrics and conduct a sensitivity analysis on the abstention decision threshold to ensure robustness.

**Why this priority**: This validates the scientific rigor of the findings, ensuring that observed improvements are not due to random chance and that the results are stable across reasonable parameter variations.

**Independent Test**: The analysis script generates a report confirming statistical significance ($p < 0.05$) and visualizes the variation in false-positive/false-negative rates across a sweep of decision thresholds.

**Acceptance Scenarios**:

1. **Given** the performance metrics from the Meta-Critic and Full-Context conditions, **When** the statistical test runs, **Then** the output includes a p-value indicating whether the difference in token consumption and latency is statistically significant ($p < 0.05$).
2. **Given** a default abstention threshold of 0.5, **When** the sensitivity analysis sweeps the threshold over the set {0.4, 0.45, 0.5, 0.55, 0.6}, **Then** the report shows how the inconsistency rate (false positives/negatives) varies across these values.
3. **Given** the collinearity check, **When** the analysis runs, **Then** the report explicitly states whether any predictors (e.g., turn number vs. token usage) are definitionally related and if collinearity diagnostics (e.g., VIF) were applied.

---

### Edge Cases

- What happens if the dataset contains trajectories with missing error logs or malformed token counts? (System should skip or impute based on a defined rule, not crash).
- How does the system handle a task where the ground truth "impossibility" is ambiguous or contested? (The system relies strictly on the benchmark's provided ground truth labels; ambiguity is recorded as a data limitation).
- What if the meta-critic predicts "abstain" on the very first turn? (The system must log this as an immediate stop and record the feature vector, even if it results in a false negative for a solvable task).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the specified subset of the "Agentic Abstention" benchmark and extract low-level state features (search result count, error frequency, token usage, turn number) and a low-level semantic proxy: "query-context embedding distance" (calculated as cosine similarity using SentenceTransformer v2.2, all-MiniLM-L6-v2). The system MUST exclude full semantic context strings from the feature vector. (See US-1)
- **FR-002**: System MUST train a gradient-boosted tree classifier (XGBoost or LightGBM) on CPU-only infrastructure using the extracted features to predict binary abstention labels. The ground truth label ("Abstention Label") MUST be derived from an independent, bounded exhaustive search solver (10x token budget limit) that determines if a task is "impossible" before the agent runs, ensuring independence from the agent's token/turn counts. (See US-2)
- **FR-003**: System MUST simulate the agent interaction loop where the meta-critic evaluates the state *before* the LLM generates the next action. The "Full-Context CONVOLVE baseline" MUST be generated by running the reference CONVOLVE implementation on the same task subset with a fixed random seed (seed=42) and a hard stop at 20 turns. (See US-2)
- **FR-004**: System MUST calculate and report Timely Abstention Recall, Average Token Consumption, and Wall-clock Latency for both the Meta-Critic and Full-Context conditions. (See US-2)
- **FR-005**: System MUST perform statistical significance testing using a Two-sample Kolmogorov-Smirnov test or Mann-Whitney U test on the distributions of total token consumption per task type. The null hypothesis is that the median difference in total token consumption per task between the Meta-Critic and Full-Context conditions is zero. (See US-3)
- **FR-006**: System MUST conduct a sensitivity analysis sweeping the decision threshold over a range of plausible values and report the variation in false-positive and false-negative rates. (See US-3)
- **FR-007**: System MUST verify that the dataset contains all required predictor variables. If a variable is missing for a record, the system MUST apply mean imputation for numeric variables or assign an "unknown" category for categorical variables. If >5% of records are missing a critical variable, the system MUST flag the dataset as invalid and halt execution. (See US-1)

### Key Entities

- **Interaction Trajectory**: A sequence of agent actions and environment responses for a single task, containing logs of search results, errors, and token usage.
- **State Feature Vector**: A numeric vector representing the low-level state of the agent at a specific turn (e.g., turn number, cumulative tokens, error count, query-context embedding distance). The embedding distance is a scalar proxy for semantic similarity, distinct from full semantic context.
- **Abstention Label**: The ground-truth binary classification (abstain/continue) derived from an independent, bounded exhaustive search solver. A label of "abstain" is assigned if the solver fails to find a solution within a 10x token budget limit.
- **Meta-Critic Model**: The trained gradient-boosted tree classifier that maps state feature vectors to abstention decisions.
- **Independent Oracle**: A bounded exhaustive search solver that determines task "impossibility" independently of the agent's execution path or token usage.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Timely Abstention Recall is measured against the Full-Context CONVOLVE baseline to determine if the meta-critic maintains recall within 5% of the baseline. (See US-2)
- **SC-002**: Average Token Consumption is measured against the Full-Context baseline. Success is defined as a reduction of ≥40% OR a statistically significant reduction (p < 0.05) with a minimum effect size (Cohen's d) ≥ 0.5. (See US-2)
- **SC-003**: Wall-clock Latency is measured against the Full-Context baseline to verify that the decoupled decision module reduces inference time. (See US-2)
- **SC-004**: Statistical Significance ($p < 0.05$) is measured using a Two-sample Kolmogorov-Smirnov test or Mann-Whitney U test on the distributions of total token consumption per task type, with the null hypothesis that the median difference is zero. (See US-3)
- **SC-005**: Threshold Sensitivity is measured by sweeping the decision cutoff over {0.4, 0.45, 0.5, 0.55, 0.6} and reporting the stability of the inconsistency rate. (See US-3)

## Assumptions

- The specified benchmark dataset (specifically the "Environment-based Abstention" subset) is available and contains the necessary ground truth labels for task impossibility.
- The "query-context embedding distance" feature can be computed using a lightweight, CPU-tractable embedding model (SentenceTransformer v2.2, all-MiniLM-L6-v2) without requiring GPU acceleration.
- A representative subset of the full dataset is sufficient for training a robust gradient-boosted tree model on a 2-core CPU instance.
- The benchmark's ground truth labels for "impossibility" are accurate and non-circular with respect to the state features used for prediction.
- Adequate computational resources (multiple CPU cores and sufficient RAM) are available to train the model and run the simulation loop within the 6-hour limit.
- The "full-context baseline" (CONVOLVE) can be simulated or approximated using the reference implementation with a fixed seed (42) and a hard stop at 20 turns to ensure a fair comparison.
- No random assignment of tasks to conditions is performed; therefore, all findings will be framed as associational, not causal.
- The threshold sweep for sensitivity analysis (0.4 to 0.6) covers the relevant range for decision boundaries in this context.