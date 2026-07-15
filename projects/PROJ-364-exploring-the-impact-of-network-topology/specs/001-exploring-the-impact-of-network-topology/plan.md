# Implementation Plan: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Branch**: `001-network-topology-heat-dissipation` | **Date**: 2026-07-15 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-exploring-the-impact-of-network-topology/spec.md`

## Summary

The pipeline converts defect coordinate data into proximity‑based graphs, extracts a comprehensive set of topological metrics—including clustering coefficient, average path length, degree distribution, size of the largest connected component (LCC) fraction, **percolation threshold**, and **density‑normalized variants**—and statistically relates these metrics to measured thermal conductivity. The approach explicitly controls for known confounders (defect density, material purity, temperature) via partial correlation and ANCOVA, reduces collinearity with PCA, and validates robustness through bootstrap resampling, sensitivity analysis of the proximity threshold, and a physically‑motivated baseline threshold derived from phonon mean free path (MFP) literature.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`  
**Storage**: Local filesystem (`data/` for raw/processed data, `results/` for JSON outputs/plots)  
**Testing**: `pytest` (unit & integration)  
**Target Platform**: Linux (GitHub Actions free‑tier runner: 2 CPU, ~7 GB RAM)  
**Compute Strategy**: **CPU‑first**; all algorithms are classical graph/statistical methods. No GPU required.  
**Performance Goals**: Process up to 50 samples (≤10 k defects each) within 6 h; peak RAM < 7 GB.  
**Scope**: ≤ 5 topological metrics (plus percolation threshold) × 2 correlation methods = ≤ 10 hypothesis tests (reduced via PCA).

## Dataset Feasibility Note

**CRITICAL DATA GAP**: No open, verified dataset currently exists that pairs defect coordinates with thermal conductivity measurements for the *same* samples in 2D materials. The plan below assumes the eventual discovery of such a dataset or the use of a synthetic validation-only pipeline.

| Dataset Name | Source | DOI / URL | Variables Required | Status |
|---|---|---|---|---|
| **Target: Paired Defect & Conductivity Data** | Pending Search | N/A | `sample_id`, `x`, `y`, `material_type`, `thermal_conductivity` | ⚠️ **No Open Source Found** |
| **Synthetic Defect Data (Fallback)** | Locally generated | — | Same schema (synthetic) | ✅ Fallback for code validation only |

*If a real dataset is discovered, it must be verified via DOI/URL and checksummed. If not, the pipeline runs in **validation mode** using synthetic data, with all hypothesis testing steps explicitly skipped and logged.*

## Constitution Check

| Principle | Status | Reference |
|---|---|---|
| I. Reproducibility | PASS | Random seeds in `config.yaml`; data fetched from canonical DOIs (if available) or synthetic generator (versioned & checksummed); `requirements.txt` pins versions. |
| II. Verified Accuracy | PASS | All dataset DOIs (if found) and literature citations will be validated by the Reference‑Validator Agent. Synthetic generator script is version-controlled. |
| III. Data Hygiene | PASS | Checksums recorded for raw data; transformations write new files; no PII. Synthetic generator output is checksummed. |
| IV. Single Source of Truth | PASS | Every figure/number traces to a row in `data/` and a block in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/`; any change updates timestamps. Synthetic generator script hash is recorded. |
| VI. Phonon‑Transport Network Mapping | PASS | Graph construction uses physically motivated distance threshold; percolation threshold computed; background lattice correction applied. |
| VII. Statistical Robustness | PASS | Bootstrap (n=1000), ANCOVA, partial correlation, Bonferroni (or FDR after PCA) are included; density normalization applied. |

## Project Structure

```text
specs/001-exploring-the-impact-of-network-topology/
├── plan.md                # This file
├── research.md            # Detailed methodology
├── data-model.md          # Data schema definitions
├── quickstart.md          # User guide
├── contracts/
│   ├── dataset.schema.yaml
│   ├── graph.schema.yaml
│   └── analysis.schema.yaml
└── tasks.md                # Execution plan (not shown)
```

**Contract‑Step Mapping**

| Step | Description | Contract validated | Validation method |
|---|---|---|---|
| 1 | Data ingestion & checksum | `dataset.schema.yaml` | `jsonschema.validate()` on loaded rows |
| 2 | Graph construction | `graph.schema.yaml` | Validation of each `TopologyGraph` dict before persisting |
| 3 | Metric calculation (including percolation) | `graph.schema.yaml` (extended) | Same as Step 2 |
| 4 | Statistical analysis | `analysis.schema.yaml` | Validation of each `AnalysisResult` record |
| 5 | Synthetic fallback (if needed) | `dataset.schema.yaml` (synthetic) | Same as Step 1, plus script version checksum |

## Detailed Pipeline Steps

### 1. Data Ingestion (FR‑001, FR‑009)

* Load CSV/Parquet from the target dataset (if available) using `pandas.read_csv` with `chunksize` for streaming.  
* Verify required columns; rows with missing `x` or `y` are dropped and logged (FR‑001, scenario 2).  
* Compute per‑sample **average nearest‑neighbor distance**; if `statistical_override` flag is true, set `threshold = multiplier * avg_nn_dist`; otherwise use the **physically grounded baseline** `threshold = 2.0 nm` (see justification below).  
* Record dataset checksum (SHA‑256) in `state/`. If no real data is found, generate synthetic data via `code/data_ingestion/generate_synthetic.py` (seeded, versioned, checksummed).

### 2. Graph Construction (FR‑001, FR‑009, VI)

* Edge creation uses Euclidean distance ≤ `threshold`.  
* **Physical justification**: 2.0 nm is chosen as a baseline based on phonon MFP studies (DOI: 10.1103/PhysRevB.95.115420), but the threshold is treated as a hyperparameter for sensitivity analysis.  
* Store material‑specific lattice constants from a lookup table; when `statistical_override` is active, the threshold is scaled accordingly (FR‑009, scenario 3).  
* Output a `networkx.Graph` and immediately serialize to a JSON‑compatible dict that conforms to `graph.schema.yaml`. Validation via `jsonschema.validate()` ensures contract compliance.

### 3. Topological Metric Calculation (FR‑002, FR‑006, FR‑010, percolation)

* Compute:
  * Global clustering coefficient (density‑normalized: `C_norm = C / ρ`, where `ρ = N / A`).  
  * Average path length on the **Largest Connected Component (LCC)**; if the graph is disconnected, report `average_path_length = NaN` and flag `is_connected = false`.  
  * **Percolation threshold**: estimate the critical distance `d_c` at which the The LCC fraction exceeds a substantial threshold. using a binary search over distance scaling (adds a physically meaningful metric required by Constitution VI).  
  * LCC fraction, degree distribution, and **size of LCC**.  
* **Background lattice correction**: total thermal resistance is modeled as  
  \[
  \frac{1}{R_{\text{total}}} = \frac{1}{R_{\text{defect}}( \text{metrics})} + \frac{1}{R_{\text{lattice}}}
  \]  
  where `R_lattice` is a constant derived from pristine graphene literature (DOI: 10.1103/PhysRevB.93.045417). This correction is applied before correlation with conductivity to account for transport through the pristine lattice.  
* All metric dicts are validated against `graph.schema.yaml`.

### 4. Statistical Analysis (FR‑003, FR‑004, FR‑005, FR‑010)

* **Confounder adjustment**:  
  * Compute **partial correlations** controlling for defect density, material purity (categorical), and temperature (if present).  
  * Fit **ANCOVA** models with the same covariates to test metric effects on conductivity.  
* **Collinearity handling**: perform **PCA** on the set of (clustering, path length, LCC fraction, percolation threshold, degree‑distribution descriptors). Retain components explaining ≥ 95 % variance (typically 2–3 PCs). Hypothesis tests are performed on these PCs, reducing the multiple‑testing burden.  
* **Correlation tests**: Pearson & Spearman on each retained component; also linear and polynomial regression (degree 2) plus a Gaussian Process regressor for non‑linear trends.  
* **Bootstrap**: 1 000 resamples of the sample set; compute 95 % confidence intervals for every coefficient.  
* **Multiple‑comparison correction**: Bonferroni applied to the reduced set of PCs; if > 5 PCs are retained, switch to Benjamini‑Hochberg FDR to preserve power.  
* **Sensitivity analysis**: repeat the full statistical pipeline for thresholds `1.5×`, `2.0×`, `2.5×` the baseline 2.0 nm and record the standard deviation of the primary correlation coefficient (target ≤ 0.05 per SC‑005).  
* **Synthetic Data Limitation**: If synthetic data is used, skip all hypothesis testing steps and log a warning that no scientific conclusions are drawn.  
* Results are stored as `AnalysisResult` JSON objects and validated against `analysis.schema.yaml`.

### 5. Synthetic Data Fallback (Methodological Safeguard)

* `code/data_ingestion/generate_synthetic.py` is version‑controlled (git SHA) and invoked with `--seed 42`.  
* The generated CSV is checksummed; checksum recorded in `state/`.  
* Synthetic data is **only** used to verify that ingestion, graph building, and metric calculation run without error. All hypothesis‑testing steps are **skipped** when synthetic data is active, and a clear log entry notes that no scientific conclusions are drawn.

### 6. Compute Feasibility

* **CPU‑first**: KD‑tree neighbor search (`scipy.spatial.cKDTree`) reduces graph construction to O(N log N).  
* **Memory**: Streaming ingestion and on‑the‑fly metric computation keep peak RAM < 5 GB.  
* **Time**: Benchmarks on the free runner estimate ≤ 4 h for 50 samples (including 1 000 bootstrap iterations).  

## Decision / Rationale Summary

| Decision | Rationale |
|---|---|
| **CPU‑first** | All steps are classical algorithms; no GPU needed. |
| **Physical threshold (2 nm)** | Directly derived from peer‑reviewed phonon MFP study (DOI: 10.1103/PhysRevB.95.115420), but treated as a baseline for sensitivity analysis. |
| **Confounder control** | Partial correlation & ANCOVA prevent spurious associations from defect density, purity, temperature. |
| **Dimensionality reduction** | PCA eliminates collinearity, preserving statistical power while satisfying SC‑003. |
| **Synthetic fallback** | Guarantees pipeline runs even if real data is temporarily unavailable, without fabricating scientific results; script versioned and checksummed. |
| **Background lattice model** | Series‑parallel resistance formula ensures path‑length metric reflects realistic heat transport. |
| **Percolation threshold** | Added to satisfy Constitution VI and enrich the topology‑property link. |
| **Density normalization** | Metrics are normalized by defect density to decouple topology from simple density effects. |