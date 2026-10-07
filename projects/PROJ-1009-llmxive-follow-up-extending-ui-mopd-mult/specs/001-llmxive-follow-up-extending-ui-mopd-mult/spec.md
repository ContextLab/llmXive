# Feature Specification: llmXive follow-up: extending "UI-MOPD: Multi-Platform On-Policy Distillation for Continual GUI Agent"

**Feature Branch**: `001-gui-topology-transfer`  
**Created**: 2026-07-22  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'UI-MOPD: Multi-Platform On-Policy Distillation for Continual GUI Agent'"

## User Scenarios & Testing

### User Story 1 - Structural Feature Extraction & Dataset Construction (Priority: P1)

The research engineer needs to parse the Uni-GUI dataset to extract non-visual structural metadata (widget tree depth, branching factor, navigation graph connectivity) and pair these with platform labels and task success outcomes to create a training-ready dataset for the structural adapter.

**Why this priority**: Without a valid, structured dataset containing the predictor variables (topology) and outcome variables (policy success), no analysis can be performed. This is the foundational data layer required for all subsequent modeling and validation.

**Independent Test**: The pipeline can be tested by running the extraction script on a small, fixed subset of Uni-GUI logs and verifying that the output CSV contains the required columns (depth, branching, connectivity, platform, success_rate) with no null values in the critical predictor fields.

**Acceptance Scenarios**:

1. **Given** a raw Uni-GUI log file containing screen hierarchies and action traces, **When** the extraction script runs, **Then** it outputs a structured record with calculated widget tree depth and navigation graph connectivity metrics.
2. **Given** a dataset record, **When** the validation check runs, **Then** it confirms that every record has a non-null platform label and a binary or scalar task success outcome.
3. **Given** a record with missing structural data (e.g., incomplete widget tree), **When** the extraction script runs, **Then** it flags the record for exclusion or imputation according to the defined data-cleaning rule.

---

### User Story 2 - Lightweight Structural Adapter Training & Feature Importance (Priority: P2)

The researcher needs to train a lightweight, CPU-tractable model (e.g., small GNN or Transformer) on the structural metadata to predict platform embeddings and identify which topological features (depth, connectivity, etc.) are most predictive of policy transfer success using SHAP values or permutation importance.

**Why this priority**: This is the core scientific experiment. It determines if structural topology alone can explain variance in cross-platform adaptation, directly answering the research question.

**Independent Test**: The training job can be tested on a local CPU environment with a subset of data to verify convergence and the generation of a feature importance report (SHAP values) without requiring GPU resources.

**Acceptance Scenarios**:

1. **Given** the structured dataset from US-1, **When** the training script executes on a CPU-only environment, **Then** it completes within the 6-hour CI limit and outputs a model artifact and feature importance scores.
2. **Given** a trained model, **When** the importance analysis runs, **Then** it ranks the topological features (e.g., navigation connectivity) by their contribution to prediction accuracy.
3. **Given** a specific topological feature, **When** the sensitivity analysis runs, **Then** it reports how the model's prediction confidence changes as the feature value is perturbed within a small concrete set (e.g., depth ∈ {3, 4, 5}).

---

### User Story 3 - Policy Simulation & Efficiency Benchmarking (Priority: P3)

The researcher needs to construct a lookup table of pre-computed policy heads and simulate the agent using the structural adapter to select the optimal head, then benchmark inference latency and memory usage against the heavy UI-MOPD baseline to quantify efficiency gains.

**Why this priority**: This validates the practical "edge deployment" motivation. It confirms that if structure predicts transfer, the resulting system is actually lighter and faster than the neural baseline.

**Independent Test**: The simulation can be tested by running the adapter on a held-out test set and verifying that the logged inference time per step is significantly lower (≥ 5x) than the baseline while maintaining a task success rate within a defined tolerance (e.g., 5%).

**Acceptance Scenarios**:

1. **Given** a held-out test set of cross-platform tasks, **When** the lightweight adapter runs, **Then** it selects a policy head based solely on structural input and executes the task in the simulation environment.
2. **Given** the execution logs, **When** the benchmark script runs, **Then** it calculates the average inference time per step and peak memory usage, confirming they are ≤ 1/5th of the UI-MOPD baseline.
3. **Given** the task outcomes, **When** the statistical comparison runs, **Then** it performs a paired t-test to confirm if the performance drop is statistically significant (p < 0.05) or within the acceptable 5% variance threshold.

---

### Edge Cases

- **What happens when** the Uni-GUI dataset contains screens with highly irregular or malformed widget hierarchies (e.g., infinite loops in navigation graphs)?
  - *System handles this by* detecting cycles during graph extraction and excluding those specific screens or truncating the graph at a maximum depth threshold (e.g., depth=10) to ensure computability.
- **How does system handle** a scenario where the structural features are identical across two distinct platforms but the policy success rates differ significantly?
  - *System handles this by* flagging these instances as "structural ambiguity" cases in the analysis, indicating that visual/semantic context is required for those specific transfers (supporting the null hypothesis).
- **What happens when** the CPU memory limit (7 GB) is exceeded during the GNN training on the full dataset?
 - *System handles this by* automatically falling back to a stratified sampling strategy (e.g., [deferred] of data) or switching to a simpler linear model (logistic regression) as a CPU-tractable approximation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract widget tree depth, branching factor, screen aspect ratio, and navigation graph connectivity from Uni-GUI logs and pair them with platform labels and task success outcomes (See US-1).
- **FR-002**: System MUST train a lightweight model (GNN or small Transformer) on CPU using only the extracted structural metadata to predict platform embeddings (See US-2).
- **FR-003**: System MUST compute feature importance scores (via SHAP or permutation) to identify which topological features drive prediction accuracy (See US-2).
- **FR-004**: System MUST simulate policy selection using a lookup table of pre-computed heads based on the adapter's output and execute tasks in the Uni-GUI environment (See US-3).
- **FR-005**: System MUST log inference latency, peak memory usage, and task success rates for every test case to enable statistical comparison against the UI-MOPD baseline (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the decision cutoff (if any) or key structural thresholds over a small concrete set (e.g., depth ∈ {3, 4, 5}) and report variance in false-positive/negative rates (See US-2).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) when evaluating the significance of multiple topological features to control family-wise error (See US-2).

### Key Entities

- **StructuralRecord**: Represents a single screen instance with attributes: `widget_depth` (int), `branching_factor` (float), `graph_connectivity` (float), `platform_id` (string), `task_success` (boolean/float).
- **PolicyHead**: Represents a pre-trained interaction policy for a specific platform, indexed by `platform_id` and `structural_embedding`.
- **AdapterModel**: The lightweight CPU-tractable model mapping `StructuralRecord` features to `PolicyHead` selection probabilities.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance in cross-platform adaptation performance explained by structural features is measured against the total variance in the dataset (R-squared metric) (See US-2).
- **SC-002**: Inference latency per step is measured against the UI-MOPD baseline latency to quantify the efficiency gain (See US-3).
- **SC-003**: Task success rate of the lightweight adapter is measured against the UI-MOPD baseline success rate to determine if the drop is within the 5% tolerance threshold (See US-3).
- **SC-004**: Feature importance rankings are measured against the known theoretical relevance of topological features (e.g., connectivity) to validate the model's interpretability (See US-2).
- **SC-005**: The statistical significance (p-value) of the performance difference between the adapter and baseline is measured against the threshold of 0.05 (See US-3).
- **SC-006**: Sensitivity analysis results are measured across the defined sweep set (e.g., depth ∈ {3, 4, 5}) to report the stability of the headline success rates (See US-2).

## Assumptions

- The Uni-GUI dataset contains sufficient structural metadata (widget trees, navigation graphs) to calculate the required topological features (depth, connectivity) for all target platforms.
- The "task success" metric in Uni-GUI is a reliable, independent ground truth that does not mathematically derive from the structural inputs themselves.
- A lightweight GNN or small Transformer can be trained on a CPU-only runner (2 cores, ~7 GB RAM) within 6 hours using a sampled or subsetted version of the dataset.
- The UI-MOPD baseline performance metrics (latency, success rate) are available or can be reproducibly generated for the same test set to serve as the comparison reference.
- The structural features (e.g., navigation connectivity) are invariant to minor layout shifts (e.g., screen resolution changes) as assumed in the generalization check.
- No GPU accelerators (CUDA, bitsandbytes) are available; all models must run in default precision on CPU.
- The "[deferred] variance" and "5–10x latency reduction" targets in the expected results are treated as the concrete thresholds for success/failure analysis, not vague placeholders.
