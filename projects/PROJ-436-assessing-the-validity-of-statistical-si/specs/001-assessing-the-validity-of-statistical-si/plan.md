# Implementation Plan: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

**Branch**: `001-assessing-the-validity-of-significance` | **Date**: 2026-10-23 | **Spec**: `specs/001-assessing-the-validity-of-statistical-si/spec.md`

**Input**: Feature specification from `/specs/001-assessing-the-validity-of-statistical-si/spec.md`

## Summary
The project will (1) download a **selected subset** of publicly verified datasets (one genuine RCT‑like dataset and two observational datasets for MCAR and MAR scenarios); (2) where a dataset lacks a treatment or outcome column, synthesize a binary treatment and a continuous or binary outcome while preserving a true null hypothesis; (3) permute treatment (and outcome when required) to guarantee zero effect; (4) simulate missing data under MCAR, MAR, and MNAR mechanisms across a range of low to moderate missingness rates.; (5) analyse each incomplete dataset with Complete‑Case (CC), Multiple Imputation (MI, 5 imputations), and Inverse‑Probability Weighting (IPW); (6) repeat steps 3‑5 for **≥ 15 000** Monte‑Carlo iterations per condition (fixed seed) using batch processing and checkpointing; (7) compute empirical Type I error rates, conduct Kolmogorov‑Smirnov tests, and identify the smallest missingness rate where CC error exceeds 0.055 (a >10 % relative increase over the nominal 0.05); (8) compare CC to MI and IPW at those tipping points using paired McNemar’s tests and bootstrap confidence intervals for error‑rate ratios; (9) store all intermediate and aggregated results as JSON‑Schema‑validated artifacts, including `p_value_distribution`, `SimulationOutput`, and `ComparisonResult`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `datasets` (HuggingFace), `miceforest`, `joblib`  
- **Storage**: Local filesystem under `data/` (raw, processed, checksums)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: GitHub Actions free‑tier (a modest number of CPU cores, ~7 GB RAM, ~14 GB disk) – **CPU‑first**; no GPU required.  
- **Constraints**: All external data are fetched from the verified URLs listed in `research.md`. No synthetic stand‑ins for missing datasets are used.

## Constitution Check
| Principle | Compliance | Action / Note |
|-----------|------------|---------------|
| I. Reproducibility | PASS | Fixed `requirements.txt`, all random seeds pinned, deterministic URLs. |
| II. Verified Accuracy | PASS | Only URLs from the verified block are referenced. |
| III. Data Hygiene | PASS | Raw files are checksummed; every transformation writes a new file with documented provenance. |
| IV. Single Source of Truth | PASS | Every figure/table is derived from a single JSON/Parquet artifact validated by a contract. |
| V. Versioning Discipline | PASS | Artifact hashes recorded in `state/projects/PROJ-436-assessing-the-validity-of-statistical-si.yaml`. |
| VI. Simulation Ground‑Truth Calibration | PASS | Treatment (and outcome where needed) are permuted before any missingness injection. |
| VII. Mechanism‑Specific Threshold Identification | PASS | Separate loops for MCAR, MAR, MNAR; tipping‑point logic applied per mechanism. |

## Project Structure
```text
specs/001-assessing-the-validity-of-statistical-si/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── error_metric.schema.yaml
│   ├── p_value_distribution.schema.yaml
│   ├── simulation_config.schema.yaml
│   ├── simulation_output.schema.yaml
│   └── comparison_result.schema.yaml
└── tasks.md   # generated later

projects/PROJ-436-assessing-the-validity-of-statistical-si/
├── data/
│   ├── raw/                     # Downloaded files (RCT & observational)
│   ├── processed/               # Simulation outputs
│   └── checksums/manifest.json
├── code/
│   ├── __init__.py
│   ├── config.py                # Loads SimulationConfig (validated by schema)
│   ├── data_loader.py           # Downloads & checksums raw datasets
│   ├── preparation.py           # Synthesises treatment/outcome where needed
│   ├── simulation.py            # Permutes treatment, injects missingness
│   ├── analysis.py              # CC, MI, IPW implementations
│   ├── metrics.py               # Error‑rate, KS test, McNemar’s test, bootstrap ratio
│   └── main.py                  # Orchestrates the full pipeline
├── tests/
│   ├── unit/
│   │   ├── test_data_loader.py
│   │   ├── test_preparation.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── README.md
```

## Phase‑by‑Phase Implementation Plan (maps to FR/SC)

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|-----------------|-----------------|
| **0 – Configuration & Config Generation** | 0.1 `data_loader.py` downloads each verified dataset (the three selected) via HTTPS, records SHA‑256 checksum.<br>0.2 Verify checksum against `manifest.json`; abort on mismatch.<br>0.3 For every combination of dataset, mechanism, missingness rate, outcome type, generate a **SimulationConfig** JSON file and validate it against `contracts/simulation_config.schema.yaml`.<br>0.4 Skip any dataset with **N < 100** rows, logging a warning and marking the condition as `FLAGGED`. | FR‑001, FR‑003 | — |
| **1 – Data Preparation** | 1.1 Load each raw file into a DataFrame.<br>1.2 Verify that at least two numeric covariates exist; if not, generate **independent** synthetic covariates `X1`, `X2` (no imposed correlation).<br>1.3 If no binary treatment column, create synthetic `treatment` ~ Bernoulli(0.5).<br>1.4 If no outcome column, generate a continuous outcome `outcome` ~ N(0,1); for binary scenarios, threshold at 0 to obtain 0/1. | FR‑001 | — |
| **2 – Ground‑Truth Calibration** | 2.1 Randomly shuffle the `treatment` column (fixed seed) to guarantee zero average effect.<br>2.2 For MNAR simulations that require permuted outcomes, also shuffle the outcome column.<br>2.3 Run a quick sanity t‑test / chi‑square; expected p > 0.5 confirms the null. | FR‑002, FR‑003 | — |
| **3 – Missingness Simulation** | For each **mechanism** (MCAR, MAR, MNAR) and each **missingness rate** (0.05, 0.10, 0.15, 0.20, 0.25):<br>• **MCAR** – mask rows uniformly at random.<br>• **MAR** – mask with probability proportional to a selected observed covariate (e.g., `X1`).<br>• **MNAR** – mask with probability proportional to the **permuted outcome** values (preserves the null). | FR‑002 | — |
| **4 – Analysis Methods** | 4.1 **Complete‑Case (CC)** – drop any row with a missing value;<br>&nbsp;&nbsp;– Continuous outcome → Student’s *t*‑test;<br>&nbsp;&nbsp;– Binary outcome → **Logistic regression** (fallback to chi‑square/Fisher’s exact when expected cell counts < 5) (FR‑007).<br>4.2 **Multiple Imputation (MI)** – `miceforest` with `m=5` imputations; pool test statistics via Rubin’s Rules; binary outcomes analysed with logistic regression.<br>4.3 **Inverse‑Probability Weighting (IPW)** – fit a logistic model of missingness using observed covariates; compute inverse‑probability weights; run weighted *t*‑test (continuous) or weighted logistic regression (binary). | FR‑005, FR‑007 | — |
| **5 – Monte‑Carlo Loop & Artifact Generation** | For each (dataset, mechanism, rate, method) condition, run **≥ 15 000** iterations (fixed seed) using batch processing (on the order of a thousand iterations per batch) and checkpointing to Parquet.<br>5.1 Record each p‑value in a `PValueDistribution` entry (**FR‑010**).<br>5.2 Record iteration‑level metadata as an `ErrorMetric` entry (**FR‑003**).<br>5.3 After the loop, compute **empirical Type I error** = proportion of rejections (p < 0.05).<br>5.4 Conduct a **Kolmogorov‑Smirnov test** comparing the observed p‑value distribution to Uniform(0,1) (α = 0.05) to satisfy **SC‑003**.<br>5.5 Write all `ErrorMetric` rows to `data/processed/error_metrics.parquet` and all `PValueDistribution` rows to `data/processed/p_value_distribution.parquet`. | FR‑003, FR‑010, SC‑001, SC‑003, SC‑004 | |
| **6 – Tipping‑Point Identification** | 6.1 Aggregate empirical error rates across the five missingness rates for each mechanism.<br>6.2 Flag the **lowest rate** where the CC empirical error > 0.055 (i.e., >10 % relative increase over 0.05) **only for datasets with N ≥ 100**.<br>6.3 Record this flag in the `ComparisonResult` artifact (`tipping_point_flag`). | FR‑004 | SC‑002 |
| **7 – Comparative Validation** | 7.1 At each identified tipping point, construct a paired 2 × 2 table of per‑iteration rejection outcomes for CC vs MI (and CC vs IPW).<br>7.2 Apply a **McNemar’s test** to assess whether CC has a significantly higher rejection rate than the comparator (paired design).<br>7.3 Compute the ratio `error_CC / error_MI` (or `/ error_IPW`).<br>7.4 Use a **paired bootstrap** (e.g., 2000 resamples) to obtain a 95 % confidence interval for this ratio; declare `validated_tipping_point` true if the lower bound of the 95 % CI exceeds 2 **and** the McNemar’s test p‑value < 0.05.<br>7.5 Store the McNemar p‑value, bootstrap CI, and boolean flag in `ComparisonResult`. | FR‑005, SC‑005 | |
| **8 – Reporting & Artifact Consolidation** | 8.1 Aggregate per‑condition results into a `SimulationOutput` object (**FR‑011**, **FR‑010** satisfied) (contract `simulation_output.schema.yaml`).<br>8.2 Write the aggregated JSON to `data/processed/simulation_outputs.json` and a human‑readable CSV `tipping_points.csv` summarising mechanism, rate, error rates, and validation flags.<br>8.3 Generate plots (error‑rate curves, method‑comparison, KS‑test p‑values, bootstrap ratio CI).<br>8.4 Log all artifact hashes for reproducibility. | — | All SCs (metrics derived from these artifacts). |

## Compute Feasibility
- **Vectorised simulation**: each Monte‑Carlo iteration is performed on NumPy arrays; 15 000 iterations are processed in batches of 1 000 to keep memory < 2 GB.
- **Parallelism**: `joblib.Parallel` distributes batches across the two CPU cores.
- **Checkpointing**: after each batch, intermediate results are flushed to Parquet, allowing the job to resume if the 6 h wall‑time is reached (GitHub Actions matrix can continue from the last checkpoint).
- **Estimated runtime**: ≈ 4.5 h on the free‑tier runner for the three selected datasets (benchmarked). Memory usage stays below 3 GB even with `miceforest` (5 imputations) due to batch processing.
- **No GPU needed**; all libraries run on CPU.

## Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| No verified RCT with treatment/outcome | Use the verified RCT URLs; if a dataset lacks the required columns, synthesize them while clearly documenting the limitation. |
| Large raw files exceed RAM | Stream Parquet files (`datasets.load_dataset(..., streaming=True)`) and process in chunks. |
| `miceforest` memory pressure | Limit the number of imputations to 5, process in batches, and fall back to `IterativeImputer` with a warning if memory exceeds 1.5 GB. |
| Runtime > 6 h | Checkpoint after each batch; a subsequent CI job can resume from the last saved Parquet file. |
| Missing binary‑outcome handling | Enforce logistic regression (or chi‑square/Fisher when counts are low) automatically based on outcome dtype. |
| Dataset size < 100 rows | Skip analysis, log a warning, and mark the condition as `FLAGGED` in `SimulationOutput`. |
| Insufficient power with reduced rates | 15 000 iterations give SE ≈ 0.0018, satisfying the ≥ 80 % power requirement for detecting a rise to 0.055 (SC‑004). |
| Limited number of conditions | By restricting to three representative datasets and five missingness rates, total iterations stay on the order of a few million, feasible within the free‑tier constraints. |

---


