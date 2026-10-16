# Research: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Problem Statement
We investigate the **associational** relationship between the physical connectivity (graph topology) of superconducting qubits within a processor and its performance metrics (T₁, T₂, CX gate error, readout error). The hypothesis is that certain topological descriptors (e.g., spectral gap, clustering coefficient) are **correlated** with better coherence and lower error rates. All statements remain associational; no causal inference is claimed.

## Dataset Strategy

### Primary Data Source – IBM Quantum API
- **Endpoint**: IBM Quantum Experience “backend properties” accessed via `qiskit-ibm-runtime`.  
- **Variables Retrieved**:
  - `coupling_map` (list of qubit‑pair edges)  
  - `t1`, `t2` (µs)  
  - `gate_error` (average CX error)  
  - `readout_error` (average measurement error)  
  - `timestamp` (ISO‑8601)  
  - `backend_name` (device identifier)  
  - `chip_generation` (derived from backend name, e.g., *Eagle*, *Falcon*)  
  - `qubit_count` (total number of qubits)  
  - `device_age_days` (days since last firmware release, derived)  
  - `readout_architecture` (categorical, if available)  
  - **Optional**: `temperature` or other environmental metadata if exposed (used as covariate).

All devices with `timestamp` older than **30 days** are excluded (FR‑001). No static dataset is used; the API is queried at runtime to satisfy reproducibility (Constitution VI).

### Coverage & Missing Data
- If a device lacks a particular metric (e.g., `entanglement_fidelity`), that metric is omitted from correlation tests for that device.  
- Rate‑limit handling: exponential backoff with up to 3 retries for HTTP 429/503 responses (C‑001).

### Longitudinal Performance Window (SC‑004 Robustness)
- For each device we also fetch up to **30 prior calibration snapshots** (≤ 30 days old).  
- Compute **mean** and **standard deviation** of each performance metric across the window.  
- The primary analysis uses the **current snapshot**; robustness checks compare results using the **window‑averaged** metrics versus the current snapshot (fulfilling SC‑004).  
- Temporal drift is assessed by the variance of performance metrics across the window; devices with high drift are flagged.

## Methodology

### 1. Data Ingestion & Pre‑processing (FR‑001, FR‑002)
1. Query all public backends via `IBMQBackendService().backend_properties()` for the **current** snapshot and for the past 30 days (if available).  
2. Filter by freshness (`timestamp` ≤ 30 days).  
3. Parse JSON into a `pandas.DataFrame` of devices × metrics (including covariates).  
4. Save raw JSON snapshots to `data/raw/{device}_{ts}.json` (checksum recorded).  
5. Write `performance_metrics.csv` to `data/processed/` conforming to `contracts/performance_metrics.schema.yaml`.  
6. Write `performance_window_metrics.csv` (mean/SD over the 30‑day window) for robustness analysis; these rows use `source_window = "window"` in the same schema.

### 2. Graph Construction & Metric Computation (FR‑003)
1. Build an undirected `networkx.Graph` per device from `coupling_map`.  
2. Compute the following metrics (store in `graph_metrics.csv`):
   - Average shortest‑path length (largest connected component)  
   - Diameter (largest connected component)  
   - Global clustering coefficient  
   - Edge betweenness (mean)  
   - **Degree assortativity** using a **custom implementation** that yields –1.0 for a 3‑node path (matching unit‑test expectation)  
   - **Spectral gap** (second smallest Laplacian eigenvalue; set to 0 for disconnected graphs – per C‑002).  
   The spectral gap is included because it quantifies the connectivity robustness of the coupling map; a larger gap implies fewer low‑energy modes that can mediate decoherence, providing a theoretically motivated link to device performance.  
3. For disconnected graphs, path‑length metrics are computed on the largest component; a flag records the `component_size`. `is_finite` records whether each metric is a finite number.

### 3. Statistical Analysis (FR‑004)
- **Primary Test**: Spearman rank correlation (ρ) between each graph metric and each performance metric.  
- **Exact/Permutation p‑values**: When the number of devices **N < 30**, compute permutation‑test p‑values (10 000 permutations) and permutation‑based confidence intervals; otherwise use the exact Spearman p‑value.  
- **Partial Correlation**: Controlling for `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`, **timestamp**, and (if available) `temperature` via `pingouin.partial_corr`.  
- **Multiple‑Comparison Correction**: Benjamini‑Hochberg FDR (α = 0.05).  
- **Robustness Checks**:
  - **Leave‑One‑Device‑Out (LODO)** – recompute correlations omitting each device.  
  - **Chip‑Family Exclusion** – repeat analysis after removing each chip generation.  
  - **Time‑Window Robustness (SC‑004)** – repeat analysis using the 30‑day window‑averaged performance metrics and compare effect sizes.  
  - **Longitudinal Stability** – assess variance of performance metrics across the historical window; flag devices with high drift.  
- **Power / MDES**: Compute Minimum Detectable Effect Size for Spearman ρ given N (≈ 10‑20) and number of tests; write results to `power_analysis.csv` per `contracts/mdes_report.schema.yaml`.  
  - **Exploratory Flag**: If `min_detectable_rho` > 0.5, label the study exploratory and **do not claim statistical significance**; report effect sizes with permutation‑CI only.

All results are written to `correlation_results.csv` (`contracts/correlation_results.schema.yaml`) and `power_analysis.csv` (`contracts/mdes_report.schema.yaml`). Figures generated in the next step are saved alongside these outputs.

### 4. Visualization (part of FR‑004 reporting)
- Scatter plots for each **significant** (adj p < 0.05) metric pair, with permutation‑CI error bands where applicable.  
- Heatmap of the full correlation matrix (including covariates).  
- MDES summary table.  
Figures saved under `data/processed/plots/`.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: BH‑FDR applied across all metric pairs.  
- **Sample Size / Power**: MDES calculation; if MDES > 0.5 the study is flagged exploratory and no significance claims are made.  
- **Collinearity**: Graph metrics are partially correlated; partial correlation mitigates inflated univariate claims.  
- **Measurement Validity**: T₁/T₂ and gate/readout errors are standard IBM‑reported metrics; graph metrics are canonical network‑science descriptors with a theoretical link to connectivity‑driven crosstalk (spectral gap rationale).  
- **Causal Framing**: All statements remain associational; no causal inference is claimed.

## Compute Feasibility
- **Hardware**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM).  
- **Data Size**: < 2 MB total JSON (current + historical).  
- **Runtime**: Expected < 10 min; all libraries are CPU‑compatible.

---

