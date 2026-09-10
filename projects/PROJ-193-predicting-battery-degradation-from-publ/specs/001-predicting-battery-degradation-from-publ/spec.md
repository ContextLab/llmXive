# Feature Specification: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature Branch**: `001-predict-battery-degradation`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1)

As a researcher, I want to download the NASA Ames and University of Wisconsin battery datasets, parse raw voltage/current/temperature CSVs, and construct normalized input sequences (first 50 cycles) with a known target (final capacity fade), so that I can establish a reproducible data foundation for model training.

**Why this priority**: Without clean, aligned, and normalized data, no model can be trained or evaluated. This is the foundational step that enables all subsequent modeling and analysis.

**Independent Test**: Can be fully tested by running the ingestion script on a local machine and verifying that the output contains a structured dataset where each cell has exactly 50 aligned time-steps per cycle for voltage, current, and temperature, with a corresponding scalar target value for final capacity fade.

**Acceptance Scenarios**:

1. **Given** the NASA and UW dataset URLs are accessible, **When** the ingestion script executes, **Then** it must successfully download and extract all CSV files for cells with complete cycling histories.
2. **Given** raw CSV files are downloaded, **When** the pre-processing script runs, **Then** it must resample all traces to a uniform time step, normalize features per cell to remove magnitude bias, and output a single structured file where the input shape is (N_cells, 50_cycles, T_steps, 3_channels) and the target is (N_cells, 1).

---

### User Story 2 - CPU-Tractable Bi-LSTM Model Training (Priority: P2)

As a researcher, I want to train a Bi-LSTM model (2 layers, 64 units) on the pre-processed sequences using Adam optimizer with early stopping, such that the model fits within the 6-hour GitHub Actions free-tier CPU limit and achieves an R² ≥ 0.80 on a held-out test set.

**Why this priority**: This is the core research engine. It must be computationally feasible on free-tier infrastructure (no GPU) to ensure the project can reach completion without external hardware dependencies.

**Independent Test**: Can be fully tested by executing the training script on a CPU-only environment (e.g., GitHub Actions runner) and verifying that the job completes within 6 hours, consumes ≤7 GB RAM, and produces a model file with reported validation R² ≥ 0.80.

**Acceptance Scenarios**:

1. **Given** the pre-processed dataset is available, **When** the training script runs on a CPU-only runner, **Then** it must complete within 6 hours and log peak memory usage ≤7 GB and peak disk usage ≤14 GB.
2. **Given** a trained model, **When** evaluated on a held-out test set of cells with unseen cycling protocols, **Then** the model must achieve an R² score ≥ 0.80 for predicting remaining useful life (capacity fade).

---

### User Story 3 - Interpretability and Signature Identification (Priority: P3)

As a researcher, I want to apply permutation importance and SHAP analysis to the trained model to identify which specific early-cycle time-steps and channels (voltage, current, temperature) contribute most to the prediction, so that I can answer the research question about which electrochemical signatures drive degradation.

**Why this priority**: This delivers the scientific insight—the "why" and "which"—that the research question demands. It transforms a black-box prediction into actionable domain knowledge.

**Independent Test**: Can be fully tested by running the interpretability script on the trained model and generating a SHAP summary plot and a permutation importance table that explicitly ranks input features by contribution.

**Acceptance Scenarios**:

1. **Given** a trained Bi-LSTM model, **When** the interpretability script runs, **Then** it must generate a SHAP summary plot showing the top 10 most influential time-steps and channels.
2. **Given** the permutation importance results, **When** analyzed, **Then** they must explicitly identify a specific subset of early-cycle features (e.g., "voltage relaxation rate in cycles 10-20") as the strongest predictors, with a quantitative contribution score.

---

### Edge Cases

- What happens when a cell in the dataset has missing cycles or incomplete end-of-life capacity data? (System must filter these cells out during ingestion).
- How does the system handle a cycling protocol that is completely unseen during training (e.g., pulse charging vs. constant current)? (System must report the R² on this specific subset separately to demonstrate generalization).
- What if the model fails to converge within the 30-minute hyperparameter sweep window? (System must fall back to default hyperparameters and log a warning).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse raw CSV files from the NASA Ames and University of Wisconsin battery repositories, filtering for cells with complete cycling histories and known end-of-life capacity (See US-1).
- **FR-002**: System MUST resample time-series data to a uniform time step, normalize features per cell, and construct input sequences using the first 50 cycles as predictors and final capacity fade as the target (See US-1).
- **FR-003**: System MUST implement a Bi-LSTM model with 2 hidden layers (64 units) in PyTorch, configured to run exclusively on CPU without GPU acceleration (See US-2).
- **FR-004**: System MUST train the model using the Adam optimizer with early stopping on a validation set, and perform a lightweight hyperparameter sweep (learning rate, hidden size) constrained to a 30-minute execution window (See US-2).
- **FR-005**: System MUST apply permutation importance and SHAP analysis to the trained model to quantify the contribution of specific time-steps and channels (voltage, current, temperature) to the prediction (See US-3).
- **FR-006**: System MUST evaluate the model on a held-out test set of cells with unseen cycling protocols and report R² and RMSE metrics (See US-2).

### Key Entities

- **BatteryCell**: Represents a single physical battery cell with attributes: `cell_id`, `protocol_type`, `voltage_trace` (time-series), `current_trace` (time-series), `temperature_trace` (time-series), `final_capacity` (scalar).
- **SequenceWindow**: Represents the processed input for a single cell: `cell_id`, `input_sequence` (50 cycles × T_steps × 3 channels), `target_fade` (scalar).
- **ModelPrediction**: Represents the output of the trained model: `cell_id`, `predicted_fade`, `confidence_interval`, `feature_importance_scores`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) is measured against the actual measured final capacity from the test set (See US-2, US-6).
- **SC-002**: Computational feasibility (job duration and memory usage) is measured against the GitHub Actions free-tier limits (6 hours, 7 GB RAM, 14 GB disk) (See US-2).
- **SC-003**: Interpretability validity is measured by the consistency of feature importance rankings across permutation importance and SHAP analysis methods (See US-3, FR-005).
- **SC-004**: Generalization performance is measured by the R² score on the subset of test cells with unseen cycling protocols (e.g., pulse charging) (See US-2).
- **SC-005**: Data completeness is measured by the percentage of cells successfully processed from the original datasets after filtering for incomplete histories (See US-1, FR-001).

## Assumptions

- The NASA Ames and University of Wisconsin battery datasets contain all required variables (voltage, current, temperature, final capacity) for the analysis; if a specific dataset lacks a required variable (e.g., temperature), the analysis will proceed with the available channels and note this limitation.
- The GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) is sufficient to train a small Bi-LSTM model (2 layers, 64 units) on the sampled dataset within the 6-hour limit.
- The "first 50 cycles" window is a defensible community-standard default for early-cycle prediction; if the research suggests a different window is more predictive, a sensitivity analysis will be performed.
- The Bi-LSTM model will be trained in default precision (float32) without quantization or mixed-precision to ensure CPU compatibility.
- The datasets are publicly accessible and do not require authentication or special licensing beyond the standard terms of use.
- The "unseen cycling protocols" test set will be constructed by splitting the data such that entire protocol types (e.g., all pulse charging cells) are held out from training.
