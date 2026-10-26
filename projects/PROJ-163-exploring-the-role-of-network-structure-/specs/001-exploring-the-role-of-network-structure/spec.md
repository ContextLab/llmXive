# Specification: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Overview

This project investigates the correlation between topological properties of superconducting qubit coupling maps (e.g., average shortest path length, clustering coefficient, spectral gap) and device performance metrics (e.g., coherence times, gate errors, readout errors, **entanglement fidelity**). The study utilizes real‑time calibration data from IBM Quantum backends and performs both cross‑sectional and robustness analyses.

## User Stories

### US1: Retrieve and Parse IBM Quantum Calibration Data
- **Goal**: Fetch latest calibration data for all accessible backends.
- **Acceptance Criteria**:
  - Data is fetched within 30 days of execution.
  - Topology (coupling map) and performance metrics are extracted.
  - Invalid or stale data is excluded with logging.
- **(See SC-001)**

### US2: Construct Connectivity Graphs and Compute Topological Metrics
- **Goal**: Convert coupling maps to graphs and compute metrics.
- **Acceptance Criteria**:
  - Graphs are undirected.
  - Metrics include shortest path, clustering, betweenness, **spectral gap**, and assortativity.
  - Devices with tunable couplers capture the **multiplex layer** (active vs. inactive edges).
  - Disconnected graphs are handled gracefully.
- **(See SC-002)**

### US3: Execute Statistical Correlation, Regression, and Robustness Analysis
- **Goal**: Correlate topology with performance, quantify effect sizes, and assess robustness.
- **Acceptance Criteria**:
  - Spearman rank correlation is computed for each topology‑performance pair.
  - Linear regression with heteroscedasticity‑robust standard errors is performed.
  - Partial correlation controlling for confounders (chip generation, qubit count, device age, readout architecture, calibration timestamp) is computed.
  - Robustness checks:
    - **Leave‑One‑Device‑Out (LODO)** analysis.
    - **30‑day historical performance window** analysis.
  - Visualizations (scatter plots, heatmaps, markdown report) are generated.
- **(See SC-003, SC-004, SC-005, SC-006, SC-007)**

## Functional Requirements

### FR-001: Data Freshness
Devices with calibration data that exceed the **acceptable freshness interval of 30 days** must be excluded from the primary analysis. *(See US1, SC-001)*

### FR-002: Metric Extraction
The system must extract T1, T2, gate errors, readout errors, **entanglement fidelity**, and coupling maps from each backend's calibration payload.  
**Justification**: Including gate and readout errors provides a comprehensive view of performance beyond coherence times, aligning with the research goal of assessing overall device quality. *(See US2)*

### FR-003: Cross‑Sectional Analysis
The study shall operate as a **cross‑sectional analysis**. Topology and performance metrics are extracted from the *same* calibration snapshot (simultaneous data).  
**Aggregation rule**: Device‑level performance values are derived by applying a statistically appropriate summary (mean or median) to per‑qubit measurements; the chosen summary (median by default) is justified as robust to outliers (see FR‑018). *(See US3)*

### FR-004: Robustness Checks
- **LODO**: Leave‑One‑Device‑Out analysis to ensure stability.  
- **Time Window**: Performance metrics from a **30‑day historical window** shall be compared against the cross‑sectional results to verify correlation stability (satisfying SC‑004). Historical snapshots are obtained via the IBM Quantum archive API (see FR‑012). *(See US3, SC‑004)*

### FR-005: Cross‑Sectional Guard
The system must raise an error if topology and performance timestamps differ by more than **1 hour**, ensuring true simultaneity.  
**Justification**: Ensuring topology and performance timestamps are within 1 hour guarantees that the metrics reflect the same physical state of the device, avoiding temporal‑mismatch bias. *(See US3)*

### FR-006: Entanglement Fidelity Extraction
Extract entanglement fidelity from the calibration data (available in IBM Quantum backend properties). *(See US2)*

### FR-007: Multiplex Layer Capture
For devices with tunable couplers, record edge status (`active` / `inactive`) as an attribute `edge_type` in the graph representation. *(See US2)*

### FR-008: Regression Analysis
Fit a linear regression model for each topology‑performance pair using heteroscedasticity‑robust standard errors; report beta coefficients with 95 % confidence intervals. *(See US3, SC‑006)*

### FR-009: Visualization Generation
Produce scatter plots for each topology‑performance pair, a heatmap of the full correlation matrix, and a markdown report bundling all figures and tables. All plots must be saved as PNG files and referenced in the final report. *(See US3, SC‑005)*  
**Justification**: Visualizing all measured performance metrics enables assessment of which aspects of device performance relate to topology. *(See US3)*

### FR-010: Power Analysis (Revised)
Perform a priori power analysis targeting **≥ 60 % power** to detect a Spearman ρ of **0.3** (small‑to‑medium effect). Report the minimum detectable effect size (MDES) **for this target** and the achieved power.  
**Justification**: A power analysis is required to ensure the study is adequately powered to detect a meaningful correlation given the limited number of publicly accessible IBM back‑ends (< 30 devices). *(See US3, SC‑007)*

### FR-011: Confounder Adjustment
Control for known confounders (chip generation, qubit count, device age in days, readout architecture, calibration timestamp) using partial correlation or multivariate regression. *(See US3)*

### FR-012: Historical Snapshot Retrieval
Retrieve and store daily calibration snapshots for the past 30 days via the IBM Quantum archive API, making them available for the Time‑Window robustness check. *(Supports FR‑004)*

### FR-013: Spectral Gap Relevance
Compute the spectral gap of the graph Laplacian and include it as a topology descriptor, justified by Falk et al. linking relatively larger spectral gaps to reduced circuit depth and improved device performance. *(See US2, SC‑002)*

### FR-014: Window‑Comparison Recording
For each topology‑performance pair, store the cross‑sectional Spearman ρ, the 30‑day window ρ, and their absolute difference (`window_delta`) in `window_comparison.csv`. This artifact enables verification of SC‑004. *(See SC‑004)*

### FR-015: Cluster‑Robust Correlation Testing
When computing Spearman correlations, apply a cluster‑robust variance estimator that accounts for shared hardware generations/families among devices. Report cluster‑adjusted p‑values.  
**Justification**: Devices share hardware generations; accounting for clustering prevents inflated significance estimates. *(Supports SC‑003)*

### FR-016: Separation of Topology and Performance Data
Explicitly ensure that topology metrics are derived solely from the coupling‑map graph structure, while performance metrics are aggregated from per‑qubit properties. This separation prevents conflation of predictor and outcome information. *(Supports FR‑003 and scientific soundness)*

### FR-017: Additional Success Metric (Optional)
Report the proportion of devices for which the cluster‑robust p‑value ≤ 0.05. *(See SC‑003)*

### FR-018: Aggregation Justification
Device‑level performance summaries use the **median** of per‑qubit measurements because the median is robust to outliers and represents typical qubit behavior (see Rousseeuw & Croux, 1993). This choice balances resistance to noisy qubits with interpretability. *(See US3)*

## Data Model

- **QubitDevice**: Represents a backend with `device_id`, `timestamp` (ISO‑8601), `coupling_map`, `properties`.
- **GraphMetric**: Stores `device_id`, `metric_name`, `value`, `is_finite` (bool), `component_size` (int), `edge_type` (enum: active/inactive) where applicable.
- **PerformanceMetric**: Stores `device_id`, `metric_name`, `value`, `timestamp` (ISO‑8601), `source_window` (enum: `current`, `historical-30d`).
- **CorrelationResult**: Stores `metric_a`, `metric_b`, `rho`, `p_value`, `adj_p_value`, `method` (e.g., spearman, regression, partial), `cluster_adjusted_p` (optional).
- **WindowComparison**: Stores `metric_a`, `metric_b`, `cross_sectional_rho`, `window_rho`, `window_delta`.

## Non‑Functional Requirements

- **NFR-001**: All code must be Python 3.11+.
- **NFR-002**: No synthetic data generation; all data from IBM Quantum API.
- **NFR-003**: CPU‑only execution constraints.
- **NFR-004**: Reproducibility via `state/projects/PROJ-163-...yaml` artifact hashes.

## Constraints

- **C-001**: API rate limits must be respected with exponential backoff.
- **C-002**: Disconnected graphs must result in a spectral gap that vanishes (value = 0).

## Success Criteria

### SC-001: Data Freshness Compliance
≥ 95 % of devices used in the primary analysis have calibration timestamps ≤ 30 days old. *(See US1, FR‑001)*

### SC-002: Graph Construction Completeness
For every device, all listed graph metrics (shortest path, clustering, betweenness, spectral gap, assortativity) are computed and stored; any failure triggers a logged error and exclusion. *(See US2, FR‑013)*

### SC-003: Correlation Reporting
All topology‑performance Spearman correlations are computed with cluster‑robust variance estimation (FR‑015). P‑values are adjusted using a Bonferroni family‑wise correction (α = 0.05). The strongest correlation **among those that remain significant after correction** is highlighted, and its cluster‑adjusted p‑value must be ≤ 0.05. *(See US3, FR‑011, FR‑015)*

### SC-004: Robustness Consistency
- LODO is performed over each device (one fold per device). The analysis is considered valid only when the study includes **≥ 10 devices**; otherwise LODO is omitted and the criterion is waived.  
- For the LODO runs, the sign of ρ must match the primary cross‑sectional sign in **≥ 90 %** of folds.  
- The 30‑day window correlation ρ must lie within **±0.05** of the cross‑sectional ρ. The absolute difference is recorded as `window_delta` in `window_comparison.csv`. *(See US3, FR‑004, FR‑014)*

### SC-005: Visualization Deliverable
Generate ≥ 6 PNG visualizations (scatter plots for each topology‑performance pair and a correlation heatmap) and a markdown report PDF; all files must be listed in the final artifact manifest. *(See US3, FR‑009)*

### SC-006: Regression Effect‑Size Reporting
For each regression, the 95 % confidence interval of the beta coefficient must **exclude zero** for at least one topology‑performance pair. *(See US3, FR‑008)*

### SC-007: Power Analysis Reporting
Power analysis must demonstrate **≥ 60 % power** to detect ρ = 0.3; the MDES must be ≤ 0.3 and reported for this target. Results are recorded in `power_analysis.csv`. *(See US3, FR‑010)*

## Assumptions

- Users have stable internet connectivity to query the IBM Quantum API.
- The IBM Quantum archive provides reliable historical snapshots over a multi‑day period.
- Devices’ coupling maps are relatively static over a multi‑week horizon.
- All required backend properties (including entanglement fidelity) are exposed via the API.