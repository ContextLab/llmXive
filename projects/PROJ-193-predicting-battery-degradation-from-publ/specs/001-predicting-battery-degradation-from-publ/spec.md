# Feature Specification: Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks

**Feature Branch**: `001-predict-battery-degradation`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "Predicting Battery Degradation from Public Cycling Data with Recurrent Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) (See US-1)

As a researcher, I want to download the **Battery Archive** dataset (DOI), parse raw voltage/current/temperature CSVs, and construct normalized input sequences (initial cycles) with a known target (final capacity fade), so that I can establish a reproducible data foundation for model training.

**Why this priority**: Without clean, aligned, and normalized data, no model can be trained or evaluated. This is the foundational step that enables all subsequent modeling and analysis.

**Independent Test**: Can be fully tested by running the ingestion script on a local machine and verifying that the output contains a structured dataset where each cell has a fixed number of aligned cycles, each resampled to **100 uniform time‑steps per cycle**, and three channels (voltage, current, temperature), with a corresponding scalar target value for final capacity fade.

**Acceptance Scenarios**:

1. **Given** the Battery Archive dataset (DOI) is accessible, **When** the ingestion script executes, **Then** it must successfully download and extract all CSV files for cells with complete cycling histories.
2. **Given** raw CSV files are downloaded, **When** the pre‑processing script runs, **Then** it must resample all traces to a uniform time‑step resolution per cycle, normalize features per cell **using statistics computed only from the first 50 cycles**, and output a single structured file where the input shape is `(N_cells, 50_cycles, 100_time‑steps, 3_channels)` and the target shape is `(N_cells, 1)`.

---

### User Story 2 - CPU‑Tractable Bi‑LSTM Model Training (Priority: P2) (See US-2)

As a researcher, I want to train a Bi‑LSTM model (multiple layers, a suitable number of units) on the pre‑processed sequences using Adam optimizer with early stopping, such that the model fits within the free‑tier CPU time limit of GitHub Actions and **must** achieve an R² ≥ 0.80 on a held‑out test set.

**Why this priority**: This is the core research engine. It must be computationally feasible on free‑tier infrastructure (no GPU) to ensure the project can reach completion without external hardware dependencies.

**Independent Test**: Can be fully tested by executing the training script on a CPU‑only environment (e.g., GitHub Actions runner) and verifying that the job completes within 6 hours, consumes ≤7 GB RAM, and produces a model file with reported validation R² ≥ 0.80, with model outputs validated against `model_output.schema.yaml`.

**Acceptance Scenarios**:

1. **Given** the pre‑processed dataset is available, **When** the training script runs on a CPU‑only runner, **Then** it must complete within 6 hours and log peak memory usage ≤7 GB and peak disk usage ≤14 GB.
2. **Given** a trained model, **When** evaluated on a held‑out test set of cells with unseen cycling protocols, **Then** the model **must** achieve an R² score ≥ 0.80; the achieved value will be reported together with a confidence interval.

---

### User Story 3 - Interpretability and Signature Identification (Priority: P3) (See US-3)

As a researcher, I want to apply permutation importance, SHAP analysis, and attention‑based attribution to the trained model to identify which specific early‑cycle time‑steps and channels (voltage, current, temperature) contribute most to the prediction, so that I can answer the research question about which electrochemical signatures drive degradation.

**Why this priority**: This delivers the scientific insight—the “why” and “which”—that the research question demands. It transforms a black‑box prediction into actionable domain knowledge.

**Independent Test**: Can be fully tested by running the interpretability script on the trained model and generating (a) a SHAP summary plot, (b) a permutation importance table, and (c) attention weight visualizations that together rank input features by contribution.

**Acceptance Scenarios**:

1. **Given** a trained Bi‑LSTM model, **When** the interpretability script runs, **Then** it must generate a SHAP summary plot showing the most influential time‑steps and channels, a permutation importance table, and attention weight visualizations.
2. **Given** the importance results, **When** analyzed, **Then** the system must produce a ranked table of **all** early‑cycle features (voltage, current, temperature across cycles 1‑50) with quantitative contribution scores; the most salient features will be used for an independent linear‑regression check (see SC‑009) and a literature‑anchored validation (see SC‑010).

### Edge Cases

- What happens when a cell in the dataset has missing cycles or incomplete end‑of‑life capacity data? (System must filter these cells out during ingestion).
- How does the system handle a cycling protocol that is completely unseen during training (e.g., pulse charging vs. constant current)? (System must report the R² on this specific subset separately to demonstrate generalization, and ensure the subset contains at least 10 cells).
- What if the model fails to converge within the 30‑minute hyperparameter sweep window? (System must fall back to default hyperparameters and log a warning).
- What if the Battery Archive download endpoint is temporarily unavailable? (System must retry up to 3 times with 60‑second backoff intervals, then fail with a descriptive error; placeholder or synthetic data MUST NOT be substituted).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse raw CSV files from a publicly available battery cycling dataset. Acceptable datasets are:  
  1. **Battery Archive** –, direct download URL: 
  2. **NASA Ames Battery Dataset** – https://data.nasa.gov/dataset/... (public CSV bundle)  
  3. **University of Wisconsin Battery Repository** – https://data.wisc.edu/... (public CSV bundle)  
  The chosen dataset must provide voltage, current, temperature time‑series and capacity measurements for cells cycled under multiple protocols, and the system must filter for cells with complete cycling histories and known end‑of‑life capacity.
- **FR-002**: System MUST resample time‑series data to a uniform **100 time‑steps per cycle**, normalize features per cell **using statistics computed only from the first 50 cycles**, and construct input sequences using the first 50 cycles as predictors and final capacity fade as the target (See US-1, FR‑010 removed). The Battery Archive dataset supplies the required three channels.
- **FR-003**: System MUST implement a Bi‑LSTM model with multiple hidden layers, **default 64 units per layer** (allowed hidden‑size range 32‑128) (See US-2). The model runs exclusively on CPU without GPU acceleration.
- **FR-004**: System MUST train the model using the Adam optimizer with early stopping on a validation set, and perform a lightweight hyperparameter sweep (learning rate, hidden size) constrained to a 30‑minute execution window, with hidden size swept within **[32, 128]** units (See US-2).
- **FR-005**: System MUST apply permutation importance, SHAP analysis, **and** attention‑based attribution to the trained model to quantify the contribution of specific time‑steps and channels (voltage, current, temperature) to the prediction (See US-3).
- **FR-006**: System MUST evaluate the model on a held‑out test set of cells with unseen cycling protocols and report R² and RMSE metrics (See US-2).
- **FR-007**: System MUST compute prediction intervals for each model prediction (e.g., via Monte Carlo dropout) and output coverage statistics (See US-2).
- **FR-008**: System MUST implement attention‑based attribution (e.g., attention weight analysis) alongside SHAP and permutation importance (See US-3).
- **FR-011**: System MUST verify that the selected dataset contains **at least 30 cells spanning a minimum of two distinct cycling protocols**, guaranteeing that a held‑out subset of **≥ 10 cells** with an unseen protocol can be constructed (See US-2).
- **FR-012**: System MUST NOT use synthetic, placeholder, or randomly generated data anywhere in the pipeline. All inputs, targets, and reported metrics MUST be computed from real Battery Archive measurements (See US-1, US-2, SC‑001).
- **FR-015**: System MUST perform feature‑selection (permutation importance / SHAP) **only on the training subset** and MUST evaluate the downstream linear‑regression analysis on a **distinct held‑out validation subset** containing at least 5 cells, thereby avoiding circular validation.
- **FR-016**: System MUST compute a hand‑crafted feature baseline (e.g., linear regression on early‑cycle summary statistics such as average voltage, capacity‑fade slope) and report its R² on the same held‑out test set; the Bi‑LSTM model’s R² must be **≥ 5 % absolute improvement** over this baseline (See US-3). *(See US-3)*
- **FR-017**: System MUST analyse the identified top‑5 early‑cycle signatures separately for each distinct cycling protocol and report protocol‑specific importance rankings, enabling assessment of how signatures vary across protocols (See US-3). *(See US-3)*
- **FR-018**: System MUST conduct a causal‑inference analysis using propensity‑score matching across protocols to estimate the causal effect of each of the top‑5 early‑cycle features on final capacity fade, reporting average treatment effects with 95 % confidence intervals (See US-3). *(See US-3)*

### Key Entities

- **BatteryCell**: Represents a single physical battery cell with attributes: `cell_id`, `protocol_type`, `voltage_trace` (time‑series), `current_trace` (time‑series), `temperature_trace` (time‑series), `final_capacity_fade` (scalar, defined in Assumptions).
- **SequenceWindow**: Represents the processed input for a single cell: `cell_id`, `input_sequence` (50 cycles × 100 time‑steps × 3 channels), `target_fade` (scalar).
- **ModelPrediction**: Represents the output of the trained model: `cell_id`, `predicted_fade`, `prediction_interval`, `feature_importance_scores`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) is measured against the **real, measured final capacity fade recorded in the Battery Archive dataset** for each held‑out test cell (See US-2, FR‑012). No simulated or proxy target may be used.
- **SC-002**: Computational feasibility (job duration and memory usage) is measured against realistic limits for the Battery Archive dataset (≤6 hours, ≤7 GB RAM, ≤14 GB disk) (See US-2). Benchmarks from prior battery‑ML studies justify these bounds.
- **SC-004**: Generalization performance **must achieve** an R² score ≥ 0.80 on the subset of test cells with unseen cycling protocols, which must contain **at least 10 cells** (See US-2, FR‑011). The achieved R² and its 95 % confidence interval will be reported.
- **SC-005**: Data completeness is measured by the percentage of cells successfully processed from the original download set after filtering for incomplete histories (processed / downloaded) (See US-1, FR‑001).
- **SC-006**: Uncertainty coverage: **at least 90 %** of true final capacity fade values must fall within the predicted **[deferred]** prediction intervals (See FR‑007).
- **SC-009**: Linear regression on the top‑5 identified features must achieve **R² ≥ 0.30** and each feature must have a **p‑value < 0.05** (statistical significance). Feature selection must be performed on the training split only, and the regression must be evaluated on a separate held‑out validation split (See FR‑015).
- **SC-010**: Independent validation of feature rankings: **at least 3 of the top‑5** ranked features must correspond to early‑cycle degradation signatures documented in the battery‑ML literature (e.g., variance of the ΔQ(V) curve, early‑cycle capacity‑fade slope, incremental‑capacity peak shifts; see Severson et al. 2019, *Nature Energy*), assessed against a documented literature list (See US-3, FR‑005). This criterion now reflects associative correspondence rather than causation.
- **SC-011**: Baseline comparison: The hand‑crafted feature baseline (FR‑016) must achieve an R² that is **≥ 5 % lower** than the Bi‑LSTM model’s R² on the same held‑out test set (See FR‑016). The numeric improvement is reported.
- **SC-012**: Protocol‑specific signature analysis: For each distinct cycling protocol, the top‑5 early‑cycle feature rankings (from FR‑017) must be reported, and the inter‑protocol variance in ranking positions must be quantified (e.g., Kendall‑τ distance ≥ 0.3 indicates meaningful variation). Results are included in the final report (See FR‑017).
- **SC-013**: Causal‑effect reporting: The causal‑inference analysis (FR‑018) must produce average treatment effect estimates for each of the top‑5 features with 95 % confidence intervals; at least one feature must show a statistically significant positive causal effect (p < 0.05) to substantiate the claim of “driving” signatures (See FR‑018).

## Assumptions

- The **Battery Archive** dataset (batteryarchive.org, DOI) contains real voltage, current, temperature time‑series and final capacity measurements for a sufficient number of cells; it aggregates cells from multiple public sources (e.g., NASA, Oxford, Sandia, Matr) providing at least two distinct cycling protocols with ≥15 cells each, satisfying FR‑011.
- The GitHub Actions free‑tier runner (a modest number of CPU cores, several gigabytes of RAM) is sufficient to train the Bi‑LSTM model on the sampled dataset within the typical time constraints of the free tier, based on benchmarked runtimes from similar studies.
- The **first 50 cycles** window is a defensible community‑standard default for early‑cycle prediction; if the research suggests a different window is more predictive, a sensitivity analysis will be performed.
- The Bi‑LSTM model will be trained in default precision (float32) without quantization or mixed‑precision to ensure CPU compatibility.
- The dataset is publicly accessible and does not require authentication or special licensing beyond the standard terms of use.
- The “unseen cycling protocols” test set will be constructed by holding out entire protocol families from the Battery Archive (e.g., all cells from one source/protocol group) as guaranteed by FR‑011.
- **Final capacity fade** is defined as  
  \[
  \text{fade} = \frac{Q_{\text{initial}} - Q_{\text{final}}}{Q_{\text{initial}}}
  \]  
  measured at the end of cycle 100 (or the last available cycle if fewer than 100). This definition is used consistently across all user stories, functional requirements, and key entities.
- All reported results are real measurements computed from Battery Archive data; no synthetic, placeholder, or randomly generated values are used anywhere in the pipeline (FR‑012).