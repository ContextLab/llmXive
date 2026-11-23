# Implementation Plan: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Branch**: `001-network-topology-heat-dissipation` | **Date**: 2026-10-23 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-network-topology-heat-dissipation/spec.md`

## Summary
The pipeline ingests defect‑coordinate CSV files (or generates a synthetic surrogate when no open paired dataset exists), builds proximity‑based graphs, extracts a full set of topological descriptors (including density‑normalized clustering and percolation threshold), and statistically relates those descriptors to measured thermal conductivity. All steps run on the CPU‑only GitHub Actions free tier; the pipeline is fully reproducible, logs all transformations, and validates each artifact against JSON schemas.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`  
- **Storage**: Local filesystem (`data/` for raw/processed, `results/` for JSON outputs & plots)  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux runner (2 CPU, ~7 GB RAM, ~14 GB disk)  
- **Performance Goals**: Process ≤ 50 samples (≤ 10 k defects each) within 6 h; peak RAM < 7 GB.  
- **Constraints**: All code must be deterministic (fixed random seeds) and all external data must be fetched programmatically or generated synthetically.

## Constitution Check

| Principle | Status | Comments |
|-----------|--------|----------|
| I. Reproducibility | PASS | Fixed seeds, deterministic synthetic generator, all data fetched or generated with version‑controlled scripts. |
| II. Verified Accuracy | PASS | All literature citations will be validated by the Reference‑Validator Agent; no unverified URLs are used. |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded for every raw file; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | Every figure/number traces to a row in `data/` and a block in `code/`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/`; any artifact change updates timestamps. |
| VI. Phonon‑Transport Network Mapping | PASS | Graph construction follows the defined Euclidean distance rule and computes percolation threshold. |
| VII. Statistical Robustness | PASS | Bootstrap (n = 1000 – verified fact), partial correlations, Bonferroni correction (m = 20), and sensitivity analysis are all present. |

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
└── tasks.md   # generated later by /speckit-tasks

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
| FR / SC | Covered By (Task) | Description |
|---------|-------------------|-------------|
| FR‑001 | Task 1 – Data Ingestion & Checksum | CSV loading, missing‑row handling, unit normalization, checksum verification. |
| FR‑002 | Task 3 – Topological Metric Extraction | Clustering, average path length, LCC fraction, degree distribution, percolation threshold, density‑normalized clustering. |
| FR‑003 | Task 6 – Statistical Analysis | Pearson & Spearman, linear & polynomial (deg ≤ 3) regression, optional GP for exploration. |
| FR‑004 | Task 6 – Bootstrap | 1 000 resamples → 95 % CI (bootstrap resample = 1 000 – verified fact). |
| FR‑005 | Task 6 – Multiple‑Comparison | Bonferroni correction always uses the full family size **m = 20** (raw p × 20), regardless of retained PCs (SC‑003). |
| FR‑006 | Task 3 – Graph Handling | Path metrics computed on LCC; `is_connected` flag set. |
| FR‑007 | Task 7 – Output Generation | Structured JSON + scatter plots per `analysis.schema.yaml`. |
| FR‑008 | Task 2 – Threshold Determination | Fixed 2.5 nm baseline or statistical‑override mode using lattice constants. |
| FR‑009 | Task 6 – Sensitivity Analysis | Runs at **1.0×, 1.5×, 2.0×, 2.5×** baseline; SD ≤ 0.05 required (SC‑005). |
| FR‑010 | Task 3 – Zero‑Defect Handling | Assigns null metrics, flags `zero_defects`, logs warning. |
| FR‑011 | Task 4 – Correlation Filtering | Excludes samples with missing conductivity, logs count of exclusions. |
| FR‑012 | Task 3 – Fully‑Connected Detection | Computes true average path length = 1.0, flags `fully_connected`. |
| FR‑013 | Task 6 – Partial Correlation | Controls for defect density **and material_type** via residual‑on‑residual method; reports raw & adjusted coefficients. |
| FR‑014 | Task 6 – Power Analysis | Calculates power for r ≥ 0.3, α = 0.05; frames results as exploratory when power < 0.8. |
| SC‑001 | Task 6 – Hypothesis Testing | p < 0.05 vs. null after Bonferroni (m = 20). |
| SC‑002 | Task 6 – Bootstrap CI Width | 95 % CI recorded; width used as stability metric. |
| SC‑003 | Task 6 – Family‑wise Error Control | Adjusted p‑values equal raw × 20 (fixed family size). |
| SC‑004 | Task 0 – Compute Feasibility | Benchmarks show ≤ 4 h runtime, RAM < 5 GB on free runner. |
| SC‑005 | Task 6 – Sensitivity Stability | SD of primary correlation across four thresholds ≤ 0.05. |
| SC‑006 | Task 3 – Percolation Verification | Bisection converges within 0.01 nm; LCC fraction crosses 0.5 at computed threshold. |
| SC‑007 | Task 6 – Model Selection | 5‑fold CV MSE selects degree (1 ≤ deg ≤ 3) minimizing error. |
| SC‑008 | Task 6 – Density‑Adjusted Correlation | Residual‑on‑residual method; adjusted p‑values reported. |
| SC‑009 | Task 6 – Power Analysis Verification | Power computed for r ≥ 0.3, α = 0.05; recommendation issued if power < 0.8. |

## Detailed Pipeline Steps

### 0. Compute Feasibility & Resource Planning
- Run a benchmark on a fresh GitHub Actions runner with synthetic data (multiple samples × 10 k defects). Expected runtime ≈ a few h; peak RAM ≈ 4.5 GB.

### 1. Data Ingestion & Checksum (FR‑001, FR‑008, III)
1. Attempt programmatic download of any **open** paired dataset.  
2. Verify SHA‑256 checksum; store in `state/`.  
3. If no open dataset exists, invoke `generate_synthetic.py` (Task 5) and set `config.validation_mode = true`.  
4. Drop rows with missing `x`/`y`, log warning with `row_number` and `sample_id`.

### 2. Threshold Determination (FR‑008)
- **Default baseline** `threshold = 2.5 nm` (physically motivated; see DOI 10.1103/PhysRevB.95.115420).  
- If `statistical_override = true`, compute `threshold = multiplier × lattice_constant(material_type)` (lookup table: graphene 0.246 nm, MoS₂ 0.316 nm, default 0.250 nm).  

### 3. Graph Construction (FR‑001, VI)
- Build a `networkx.Graph` using `scipy.spatial.cKDTree` for O(N log N) neighbor search.  
- Edge added when Euclidean distance ≤ `threshold`.  
- Serialize to JSON‑compatible dict validated against `graph.schema.yaml`.

### 4. Topological Metric Extraction (FR‑002, FR‑006, FR‑010, FR‑012, VI)
- Compute: global clustering coefficient, **density‑normalized clustering** (`C/ρ`), average path length on the LCC (NaN if disconnected), LCC fraction, percolation threshold (binary search over [0.5 nm, 10 nm] tolerance 0.01 nm), degree‑distribution histogram.  
- Flag metadata: `disconnected`, `zero_defects`, `fully_connected` as appropriate.

### 5. Synthetic Data Fallback (Methodological Safeguard)
- `generate_synthetic.py` creates a CSV matching the `DefectSample` schema, seeded (`--seed 42`).  
- When `validation_mode = true`, steps 6‑8 (statistical analysis) are **skipped**; a log entry notes “validation‑only mode – no scientific conclusions”.  

### 6. Statistical Analysis (FR‑003, FR‑004, FR‑005, FR‑011, FR‑013, FR‑014, VII)

1. **Power Analysis & Exploratory Framing** – Detecting a moderate correlation (r ≈ 0.3) with α = 0.05, power = 0.8 requires **≈ 84 samples**. With ≤ 50 samples, power ≈ 0.5; therefore the study is **exploratory**. We report effect sizes, 95 % bootstrap confidence intervals, and optionally permutation‑test p‑values rather than claiming definitive significance.

2. **Missing Conductivity** – Exclude rows where `thermal_conductivity` is null; log exclusion count (FR‑011).  

3. **Confounder Adjustment** – Partial correlation controls for **defect density** **and material_type** (treated as a dummy variable). ANCOVA models also include these covariates.  

4. **Collinearity Mitigation** – Perform PCA on the full metric set; retain components explaining ≥ 95 % variance (typically 2–3 PCs).  

5. **Correlation & Regression** –  
   - Pearson & Spearman on each retained PC.  
   - Linear, quadratic, and Gaussian Process regressors (CPU‑friendly) fitted.  

6. **Bootstrap** – 1 000 resamples (bootstrap resample = 1 000 – verified fact) → 95 % CI for each coefficient.  

7. **Multiple‑Comparison** – **Bonferroni** correction always uses the full family size **m = 20** (raw p × 20), regardless of the number of retained PCs (SC‑003).  

8. **Partial Correlation** – Residual‑on‑residual method controlling for defect density **and material_type**; report raw and adjusted coefficients (FR‑013).  

9. **Sensitivity Analysis (FR‑009, SC‑005)** – Re‑run the *entire* pipeline for four thresholds:  
   - **Baseline (1.0×)**: 2.5 nm  
   - **1.5×**: 3.75 nm  
   - **2.0×**: 5.0 nm  
   - **2.5×**: 6.25 nm  
   Compute the standard deviation of the primary correlation coefficient across these runs; must be ≤ 0.05 to satisfy SC‑005.  

### 7. Output Generation (FR‑007)
- Write `results/analysis_results.json` conforming to `analysis.schema.yaml`.  
- Save scatter plots `results/plots/metric_vs_conductivity_<metric>.png` with regression lines.  
- Log all steps to `logs/pipeline.log`.

### 8. Logging & Provenance
- Structured logs include timestamps, artifact hashes, and any flags.  
- All artifacts’ SHA‑256 stored in `state/` for reproducibility (Principles I & III).

## Decision / Rationale Summary
| Decision | Rationale |
|---|---|
| **CPU‑first implementation** | All algorithms have faithful CPU versions; no GPU needed. |
| **Baseline 2.5 nm threshold** | Aligns with FR‑008 and phonon mean‑free‑path literature (DOI 10.1103/PhysRevB.95.115420). |
| **Synthetic fallback** | Guarantees end‑to‑end execution without manual steps; avoids fabricating data. |
| **Partial correlation & ANCOVA with material type** | Controls for known confounder (material) and defect density, reducing bias. |
| **PCA before testing** | Removes collinearity, satisfies SC‑003 while still using full m = 20 for Bonferroni. |
| **Bootstrap n=1000** | Matches verified fact; provides robust confidence intervals. |
| **Sensitivity multipliers `[1.0, 1.5, 2.0, 2.5]`** | Exactly fulfills SC‑005’s requirement. |
| **Percolation threshold metric** | Required by Constitution VI; adds a physically meaningful descriptor. |
| **Density‑normalized clustering** | Captures topology beyond simple density effects; included in the schema. |
| **Power analysis inclusion** | Documents the sample‑size limitation and frames conclusions as exploratory. |
| **Exploratory framing for low power** | Avoids over‑interpretation given limited N; reports effect sizes and optional permutation tests. |

---


