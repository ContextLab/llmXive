# Research: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

## Executive Summary

We examine whether the **topological arrangement of defects** in 2D materials (graphene, MoS₂) is associated with their **thermal conductivity**. By representing defect coordinates as proximity‑based graphs we extract a suite of metrics—including clustering, average path length, LCC fraction, **percolation threshold**, and **density‑normalized descriptors**—and relate them to conductivity using statistically rigorous, confounder‑adjusted analyses.

## Dataset Strategy

**CRITICAL DATA GAP**: No open, verified dataset currently exists that pairs defect coordinates with thermal conductivity measurements for the *same* samples in 2D materials. The research question remains unanswerable without such data. The plan below assumes the eventual discovery of a real dataset or the use of a synthetic validation-only pipeline.

| Dataset Name | Source | DOI / URL | Variables Required | Status |
|---|---|---|---|---|
| **Target: Paired Defect & Conductivity Data** | Pending Search | N/A | `sample_id`, `x`, `y`, `material_type`, `thermal_conductivity` | ⚠️ **No Open Source Found** |
| **Synthetic Defect Data (Fallback)** | Locally generated | — | Same schema (synthetic) | ✅ Fallback for code validation only |

*All datasets are openly accessible without authentication. If a real dataset is found, it will be verified via DOI/URL and checksummed. If not, the pipeline runs in validation mode using synthetic data, with all hypothesis testing steps explicitly skipped.*

## Methodology

### 1. Graph Construction (FR‑001, FR‑009)

* **Edge creation** uses Euclidean distance ≤ `threshold`.  
* **Baseline threshold (2.0 nm)** is taken from the phonon mean free path (MFP) study **DOI: 10.1103/PhysRevB.95.115420**, which reports MFP ≈ 2 nm for defective graphene. This makes the graph a proxy for phonon‑scattering pathways, but the threshold is treated as a hyperparameter for sensitivity analysis, not a fixed physical constant.  
* When `statistical_override` is enabled, the threshold is set to `multiplier × avg_nn_distance`. Material‑specific lattice constants are looked up from a small JSON table; they are applied only in override mode (FR‑009, scenario 3).  
* Missing coordinates are dropped with a logged warning (US‑1, scenario 2).

### 2. Topological Metric Calculation (FR‑002, FR‑006, VI)

* **Metrics**: global clustering coefficient, average path length (computed on the LCC), LCC fraction, **percolation threshold** (critical distance where LCC > 0.5), degree distribution histogram, and **density‑normalized** versions (e.g., `C_norm = C / ρ`).  
* **Background lattice correction**: thermal resistance is modeled as  

  \[
  \frac{1}{R_{\text{total}}} = \frac{1}{R_{\text{defect}}(\text{metrics})} + \frac{1}{R_{\text{lattice}}}
  \]

  where `R_lattice` is taken from pristine graphene literature (DOI: 10.1103/PhysRevB.93.045417). This corrected resistance is used in correlation analyses, addressing the concern that sparse defect graphs ignore the pristine lattice.

* Disconnected graphs trigger `average_path_length = NaN`, `is_connected = false`, and the metric is flagged in metadata (US‑2, scenario 2).

### 3. Statistical Analysis (FR‑003, FR‑004, FR‑005, FR‑010)

* **Confounder adjustment**:  
  * **Partial correlation** controlling for defect density, material purity, and temperature (if present).  
  * **ANCOVA** models with the same covariates to test the effect of each metric on conductivity.  
* **Collinearity handling**: Perform **PCA** on the full metric set; retain components explaining ≥ 95 % variance (typically 2–3 PCs). Hypothesis testing is performed on these PCs, reducing the effective number of tests.  
* **Correlation & Regression**: Pearson & Spearman on each retained PC; linear, quadratic, and Gaussian Process regressors fitted.  
* **Bootstrap**: 1 000 resamples generate 95 % confidence intervals for all coefficients (FR‑004).  
* **Multiple‑comparison correction**: Bonferroni applied to the reduced set of PCs; if > 5 PCs survive, switch to Benjamini‑Hochberg FDR to retain power (SC‑003).  
* **Sensitivity analysis**: repeat the entire pipeline for thresholds `1.5×`, `2.0×`, `2.5×` the baseline 2.0 nm and compute the standard deviation of the primary correlation coefficient (target ≤ 0.05 per SC‑005).  
* **Synthetic Data Limitation**: If synthetic data is used, skip all hypothesis testing steps and log a warning that no scientific conclusions are drawn.

### 4. Synthetic Data Use (Methodological Safeguard)

* Synthetic data are generated **only** to validate the code path (graph building, metric extraction). The synthetic generator (`generate_synthetic.py`) is version‑controlled, its random seed (`--seed 42`) is fixed, and the resulting file is checksummed. No hypothesis testing is performed on synthetic data; results are logged as “validation only”.

### 5. Observational Framing

* The analysis is **associational**; no causal claims are made. All statements in the manuscript will be qualified accordingly (Constitution VII).

## Compute Feasibility

* All steps run on CPU; neighbor search uses `scipy.spatial.cKDTree` for O(N log N) scaling.  
* Streaming ingestion ensures RAM stays < 5 GB even for the largest datasets.  
* Estimated runtime on the free GitHub Actions runner: ≤ 4 h for 50 samples, including bootstrap (well within the 6‑hour limit).

## Decision / Rationale

| Decision | Rationale |
|---|---|
| **Physical threshold (2 nm)** | Directly linked to phonon MFP literature (DOI: 10.1103/PhysRevB.95.115420), but treated as a baseline for sensitivity analysis. |
| **Confounder control (partial correlation & ANCOVA)** | Prevents spurious associations from defect density, purity, temperature (addresses methodology‑fc368cad). |
| **PCA before testing** | Mitigates collinearity among metrics, preserving statistical power (addresses methodology‑5b393d70). |
| **Synthetic fallback with checksum** | Guarantees reproducibility without fabricating scientific results (addresses methodology‑147600a8 & plan‑consistency‑83a38293). |
| **Background lattice correction formula** | Provides a physically grounded total resistance estimate (addresses scientific‑2bf6740e). |
| **Percolation threshold metric** | Satisfies Constitution VI requirement (addresses plan‑consistency‑d749fed9). |
| **Density normalization** | Decouples topological structure from simple defect density (addresses methodology‑4ebf9aed). |
| **Data availability gap** | Explicitly acknowledges no open paired dataset exists; research depends on future data discovery. |