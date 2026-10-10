# Implementation Plan: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Branch**: `001-network-topology-heat-dissipation` | **Date**: 2026-10-10 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-network-topology-heat-dissipation/spec.md`

## Summary
The pipeline ingests defect‑coordinate CSV/Parquet files, builds proximity‑based graphs, extracts a defined set of topological metrics, and statistically relates those metrics to measured thermal conductivity. All steps run on CPU‑only hardware (GitHub Actions free tier). When an open paired dataset is unavailable, the pipeline automatically falls back to a versioned synthetic data generator that validates the code path without performing scientific hypothesis testing.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`  
- **Storage**: Local filesystem (`data/` for raw/processed, `results/` for JSON outputs & plots)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux runner (2 CPU, ~7 GB RAM, ~14 GB disk)  
- **Compute Strategy**: **CPU‑first**; all algorithms are classical (KD‑tree neighbor search, linear algebra, bootstrap). No GPU required.  
- **Performance Goals**: Process ≤ 50 samples (≤ 10 k defects each) within 6 h; peak RAM < 7 GB.  

## Constitution Check
| Principle | Status | Comments |
|-----------|--------|----------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic synthetic generator, all data fetched programmatically or generated with version‑controlled script. |
| II. Verified Accuracy | PASS | All literature citations (DOIs) will be validated by the Reference‑Validator Agent; dataset URLs (if discovered) are verified. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded for every raw file; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | Every figure/number is traced to a row in `data/` and a block in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/`; any artifact change updates timestamps. |
| VI. Phonon‑Transport Network Mapping | PASS | Graph construction uses a physically motivated distance threshold (2 nm) and computes percolation threshold. |
| VII. Statistical Robustness | PASS | Bootstrap (n = 1000), ANCOVA, partial correlations, Bonferroni/FDR correction, and sensitivity analysis are all present. |

## Project Structure
```text
specs/001-network-topology-heat-dissipation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── graph.schema.yaml
│   └── analysis.schema.yaml
└── tasks.md   # (generated later by /speckit-tasks)

code/
├── data_ingestion/
│   ├── load.py
│   └── generate_synthetic.py
├── graph/
│   ├── construct.py
│   └── metrics.py
├── analysis/
│   ├── stats.py
│   └── bootstrap.py
├── utils/
│   ├── checksum.py
│   └── config.py
├── main.py
└── requirements.txt

tests/
├── unit/
│   ├── test_checksum.py
│   └── test_graph_metrics.py
└── integration/
    └── test_full_pipeline.py
```

## FR / SC Mapping
| FR / SC | Covered By | Description |
|---------|------------|-------------|
| FR‑001 | Data Ingestion (Task 1) | CSV/Parquet loading, missing‑row handling, checksum verification. |
| FR‑002 | Metric Calculation (Task 3) | Clustering, average path length, LCC fraction, degree distribution, percolation threshold, **density‑normalized clustering**. |
| FR‑003 | Statistical Analysis (Task 4) | Pearson & Spearman, linear / polynomial / GP regression. |
| FR‑004 | Bootstrap (Task 4) | 1 000 resamples → 95 % CI (bootstrap resample = 1,000 – verified fact). |
| FR‑005 | Multiple‑Comparison (Task 4) | Bonferroni (fallback to Benjamini‑Hochberg if > 5 PCs). |
| FR‑006 | Disconnected Graph Handling (Task 3) | Path metrics computed on LCC; `is_connected` flag set. |
| FR‑007 | JSON Output & Plots (Task 5) | Structured JSON per `analysis.schema.yaml`; scatter plots saved. |
| FR‑009 | Configurable Threshold (Task 1‑2) | Fixed physical distance *or* statistical multiplier mode. |
| FR‑010 | Sensitivity Analysis (Task 6) | Test thresholds at **1.0× (baseline 2 nm), 2.0×, and 2.5×** the baseline; report SD ≤ 0.05 (SC‑005). |
| SC‑001 | Hypothesis Test (Task 4) | p < 0.05 vs. null of zero correlation. |
| SC‑002 | Bootstrap CI Width (Task 4) | 95 % CI recorded; width used as stability metric. |
| SC‑003 | Family‑wise Error Control (Task 4) | Bonferroni/FDR applied. |
| SC‑004 | Compute Feasibility (Task 0) | Runtime ≤ 6 h, RAM < 7 GB on free runner (benchmark). |
| SC‑005 | Sensitivity Stability (Task 6) | SD of primary correlation across thresholds ≤ 0.05. |
| **Power Analysis** | Statistical Planning (Task 6) | Detect moderate effect (r≈0.3) with α=0.05, power = 0.8 → requires **≈ 84 samples**. With a maximum of 50 samples the study is exploratory; this limitation is documented (see Power Analysis subsection). |

## Detailed Pipeline Steps

### 0. Compute Feasibility & Resource Planning
- Benchmark on a fresh GitHub Actions runner with a synthetic dataset comprising multiple samples, each containing a large number of defects. Expected runtime is on the order of several hours, with peak memory usage in the low‑single‑digit gigabyte range.

### 1. Data Ingestion & Checksum (FR‑001, FR‑009, III)
1. **Attempt download** of the paired defect‑conductivity dataset from any open URL (Materials Cloud, Zenodo).  
2. **Checksum verification** using `code/utils/checksum.py`; SHA‑256 stored in `state/`.  
3. **Graceful degradation**: if download fails **or** no verified URL exists, automatically invoke `generate_synthetic.py` (Task 5) and set `config.validation_mode = true`. No error is raised; the pipeline proceeds in validation‑only mode.  
4. **Row validation**: drop rows with missing `x` or `y`, log warning (US‑1 scenario 2).  

### 2. Threshold Determination (FR‑009)
- Compute per‑sample average nearest‑neighbor distance (`avg_nn`).  
- If `config.statistical_override = true`, set `threshold = config.multiplier * avg_nn`.  
- Otherwise use the **baseline physical threshold** `threshold = 2.0 nm` (phonon mean free path study, DOI 10.1103/PhysRevB.95.115420).  
- Material‑specific lattice constants are read from a lookup table and applied **only** when override mode is active (US‑1 scenario 3).  

### 3. Graph Construction (FR‑001, VI)
- Build a `networkx.Graph` where an edge exists iff Euclidean distance ≤ `threshold`.  
- Use `scipy.spatial.cKDTree` for O(N log N) neighbor search.  
- Serialize the graph to a JSON‑compatible dict validated against `graph.schema.yaml`.  

### 4. Topological Metric Extraction (FR‑002, FR‑006, VI)
- Compute:
  * Global clustering coefficient (`C`).
  * **Density‑normalized clustering** `C_norm = C / ρ` where `ρ = N / A`. *(new field added to schema)*
  * Average path length on the **Largest Connected Component (LCC)**; if graph is disconnected, set `average_path_length = NaN` and flag `is_connected = false`.  
  * LCC fraction `lcc_fraction = |LCC| / N`.  
  * **Percolation threshold**: binary‑search over distance scaling to find the smallest distance where `lcc_fraction > 0.5`.  
  * Degree distribution histogram (`[degree, frequency]` pairs).  
- All metric dicts validated against `graph.schema.yaml`.  

### 5. Synthetic Data Fallback (Methodological Safeguard)
- `generate_synthetic.py` creates a CSV with the same schema as the real dataset, using a fixed seed (`--seed 42`).  
- The file is checksummed; checksum recorded in `state/`.  
- When `config.validation_mode = true`, steps 6‑8 (statistical analysis) are **skipped** and a log entry notes “validation‑only run – no scientific conclusions drawn”.  

### 6. Statistical Analysis (FR‑003, FR‑004, FR‑005, FR‑010, VII)
**Executed only when real data is present.**
1. **Power Analysis** – Detecting a moderate correlation (r≈0.3) with α = 0.05 and power = 0.8 requires **≈ 84 samples**. Our maximum of 50 samples therefore limits statistical power (≈ 0.5 for r≈0.3). The study is explicitly framed as exploratory and this limitation is reported in the final results.  
2. **Confounder adjustment**: partial correlations controlling for defect density, material purity, and temperature (if present); ANCOVA models include the same covariates.  
3. **Collinearity mitigation**: PCA on the full metric set; retain components explaining ≥ 95 % variance (typically 2–3 PCs). Hypothesis tests are performed on these PCs, reducing the number of comparisons.  
4. **Correlation & Regression**:  
   - Pearson & Spearman on each retained PC.  
   - Linear, quadratic (degree 2), and Gaussian Process regressors fitted.  
5. **Bootstrap**: 1 000 resamples (bootstrap resample = 1,000 – verified fact) → 95 % confidence intervals for all coefficients.  
6. **Multiple‑comparison correction**: Bonferroni on the reduced PC set; if > 5 PCs are retained, switch to Benjamini‑Hochberg FDR (SC‑003).  
7. **Sensitivity analysis (FR‑010, SC‑005)**: Re‑run the *entire* pipeline for three thresholds:  
  * **Baseline (1.0×)**: 2.0 nm  
  * **2.0×**: 4.0 nm  
  * **2.5×**: 5.0 nm  
  Record the primary correlation coefficient for each run; compute its standard deviation. The SD must be ≤ 0.05 to satisfy SC‑005.  
8. **Result serialization**: Each `AnalysisResult` conforms to `analysis.schema.yaml` and is written to `results/analysis_results.json`.  

### 7. Output Generation (FR‑007)
- Scatter plots (`results/plots/metric_vs_conductivity_<metric>.png`) with regression lines (matplotlib + seaborn).  
- Consolidated JSON output containing metrics, correlations, p‑values, adjusted p‑values, confidence intervals, regression parameters, and sensitivity summary.  

### 8. Logging & Provenance
- All steps emit structured logs to `logs/pipeline.log`.  
- Every artifact’s SHA‑256 hash stored in `state/` for reproducibility (Principles I & III).  

## Decision / Rationale Summary
| Decision | Rationale |
|---|---|
| **CPU‑first** | All algorithms have faithful CPU implementations; no GPU needed. |
| **Baseline 2 nm threshold** | Directly linked to phonon MFP literature; serves as a physically motivated reference for sensitivity analysis. |
| **Graceful synthetic fallback** | Guarantees end‑to‑end execution without manual steps; avoids deadlock when real data is absent. |
| **Partial correlation & ANCOVA** | Prevents confounding by defect density, purity, temperature. |
| **PCA before testing** | Removes collinearity, satisfies SC‑003 (family‑wise error control). |
| **Bootstrap n=1000** | Aligns with verified fact; provides robust CI. |
| **Sensitivity multipliers `[1.0, 2.0, 2.5]`** | Exactly matches SC‑005’s requirement; eliminates malformed list. |
| **Percolation threshold metric** | Required by Constitution VI; adds a physically meaningful descriptor. |
| **Density‑normalized clustering** | Controls for simple defect density effects and is now captured in the schema. |
| **Power analysis inclusion** | Documents the sample‑size limitation and frames conclusions appropriately. |

---


