# Research: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Problem Statement
How does the physical connectivity (graph topology) of superconducting qubits within a processor influence entanglement fidelity and coherence times? This research treats the quantum processor as a graph where nodes are qubits and edges are direct coupling links. We hypothesize that topological properties (e.g., spectral gap, clustering) correlate with performance metrics (T1, T2, gate error).

**Design Clarification**: This is a **Cross-Sectional** study. The predictor (topology) is static for a given device. The analysis compares distinct devices (Device A vs Device B) rather than temporal states of a single device.

## Dataset Strategy

### Primary Data Source: IBM Quantum API
The project relies on the **live IBM Quantum API** for calibration data.
- **Source**: IBM Quantum Experience "backend properties" API (accessed via `qiskit-ibm-runtime`).
- **Rationale**: Per Spec FR-001 and Constitution Principle VI, data must be timestamped and fresh (≤ 30 days). No static dataset exists in the "Verified datasets" list that satisfies the requirement for current coupling maps and performance metrics for *all* public backends.
- **Variables Retrieved**:
  - `coupling_map`: List of directed edges (qubit pairs).
  - `t1`, `t2`: Coherence times (microseconds).
  - `gate_error`: Average error for specific gates (e.g., CX, U3).
  - `readout_error`: Measurement error rates.
  - `timestamp`: Unix timestamp of the calibration snapshot.
  - `backend_name`: Device identifier.
  - `backend_version` / `generation`: Derived from backend name (e.g., "Eagle", "Falcon") to control for manufacturing confounds.

### Dataset Coverage & Mismatch Handling
- **Coverage**: The API returns data for all publicly accessible IBM backends at runtime.
- **Missing Variables**: If a device lacks `entanglement_fidelity` (often not directly reported in basic calibration), that specific metric is excluded from correlation analysis (Spec FR-003, US-3, Scenario 4).
- **Data Freshness**: Any device with a calibration timestamp older than 30 days is excluded (Spec FR-001).
- **Rate Limits**: The fetcher implements exponential backoff and retries (3x) for 503 errors (Edge Case).
- **Statistical Power**: The sample size is limited. The analysis will **not** claim definitive causal inference. The primary output for statistical validity is the **Minimum Detectable Effect Size (MDES)**.

## Methodology

### 1. Data Ingestion & Preprocessing (FR-001)
- **Fetch**: Query `ibm_quantum` provider for `backend_properties`.
- **Filter**: Exclude devices with `timestamp` > 30 days old.
- **Parse**: Extract `coupling_map` and performance metrics into a structured DataFrame.
- **Sanity Check**: Verify non-null values for T1/T2. Log warnings for malformed data (US-1, Scenario 2).
- **Chip Family Extraction**: Derive `chip_generation` (e.g., 'Eagle', 'Falcon') from `backend_name` or `properties` to serve as a covariate.

### 2. Graph Construction & Metric Calculation (FR-002)
- **Graph Model**: Construct undirected `networkx.Graph` where nodes = qubits, edges = coupling pairs.
- **Metrics Computed**:
  1.  **Average Shortest-Path Length**: Mean distance between connected nodes.
  2.  **Diameter**: Maximum shortest-path length.
  3.  **Global Clustering Coefficient**: Density of triangles.
  4.  **Edge Betweenness**: Distribution of edge centrality.
  5.  **Degree Assortativity**: Correlation of node degrees between connected neighbors.
  6.  **Spectral Gap**: Second smallest eigenvalue of the Laplacian.
- **Disconnected Handling**: If the graph is disconnected, `spectral_gap` = 0. Path-length metrics are computed only for the largest connected component; the device is flagged for exclusion in path-length correlations (US-2, Scenario 3).
- **Validation**: Metrics checked for `NaN`/`Infinity`.

### 3. Statistical Analysis (FR-003, FR-004, FR-006, FR-007)
- **Correction to Spec FR-003**: The "historical window" requirement is **not implemented** as a temporal lag because topology is static. The analysis is **Cross-Sectional**.
- **Correlation Test**:
  - **Primary**: Spearman rank correlation ($\rho$) between each graph metric and each performance metric.
  - **Controlled**: **Partial Correlation** and **Ridge Regression** (using `sklearn`) to control for `chip_generation` and handle multicollinearity among graph metrics (e.g., diameter vs. path length).
- **Multiple Comparison Correction**: Benjamini-Hochberg (BH) FDR procedure applied to all p-values ($\alpha=0.05$).
- **Robustness Checks**:
  - **Chip-Family Exclusion**: Re-run analysis excluding specific generations (e.g., remove all 'Eagle' chips) to verify findings are not driven by a single manufacturing process.
  - **Sensitivity Analysis**: Sweep p-value threshold $\{0.01, 0.05, 0.1\}$ to test stability of significant findings (FR-006).
  - **Leave-One-Device-Out**: Verify results are not driven by a single outlier device.
- **Power Analysis**: Calculate Minimum Detectable Effect Size (MDES) for Spearman $\rho$ given $N$ (number of devices) and tests. If $N < 30$, report 95% CI and flag low power (FR-007). **This is the primary measure of statistical validity.**
- **Causal Framing**: All results framed as **associational**. No causal claims (Spec Assumption: "analysis is purely observational").

### 4. Visualization & Reporting (FR-005)
- **Outputs**:
  - Scatter plots for significant correlations (adj_p < 0.05).
  - Heatmap of the full correlation matrix (including chip generation).
  - Summary table with $\rho$, raw p, adj p, and significance flag.
  - MDES report.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Addressed via BH-FDR (FR-004).
- **Sample Size**: Acknowledged limitation. $N \approx 10-20$ (public backends). Power analysis (FR-007) will explicitly state MDES. Findings are **exploratory**.
- **Collinearity**: Graph metrics (e.g., diameter and average path length) are definitionally related. The plan uses **Partial Correlation** and **Ridge Regression** to control for this, rather than claiming independent effects from univariate tests.
- **Measurement Validity**: T1/T2 and gate errors are standard industry metrics (IBM Qiskit documentation). Graph metrics are standard network science descriptors.
- **Causal Assumptions**: None. The study is observational and cross-sectional.
- **Spec Gap**: FR-003's "historical window" is a category error for static topology. The plan implements a cross-sectional design instead, documenting this deviation.

## Compute Feasibility
- **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
- **Strategy**:
  - Data volume is small (~20 devices, < 1 MB raw data).
  - No GPU required. `networkx`, `scipy`, and `sklearn` are CPU-optimized.
  - No model training; only statistical tests and graph algorithms.
  - Runtime expected < 10 minutes.