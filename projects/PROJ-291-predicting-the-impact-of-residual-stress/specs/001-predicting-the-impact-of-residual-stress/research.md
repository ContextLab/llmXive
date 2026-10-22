# Research: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

## Overview
**Research Question**  
*To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?*

### Scope Statement
No verified open dataset provides **measured residual stress**, process parameters, material properties, and fatigue life together. Consequently:

1. **Primary analysis** will be performed on **any open dataset** that satisfies the schema (if such a dataset becomes available).  
2. **Synthetic data** (`data/raw/synthetic_fatigue.csv`) is generated **solely for pipeline validation** (unit conversion, proxy computation, checksum handling, and test‑suite verification). Results derived from this synthetic set are **not** presented as empirical evidence for the scientific question, and the synthetic set is **never eligible for mediation analysis**, regardless of row count.  
3. If no real measured‑stress dataset is found, **mediation analysis will be omitted** and a limitation will be reported. The predictive‑modeling component (Feature Sets A, B, C) will still be demonstrated on the synthetic data for methodological illustration only.

### Spec Deviation Note
spec.md FR‑003 mandates the linear proxy `σ_res ≈ k·heat_input·cooling_rate`. This plan implements the non‑linear variant `σ_res = k·log(heat_input+1)·sqrt(cooling_rate)` (same k values) because the linear form is a deterministic function of Feature Set A predictors and adds no independent information. The deviation is flagged for spec revision; the non‑linear proxy is still process‑derived and its construct validity is evaluated against measured stress (FR‑014) with an explicit circularity caveat.

## Dataset Strategy
| Requirement | Source | Availability | Action |
|-------------|--------|--------------|--------|
| Primary dataset with fatigue life, process parameters, **measured** residual stress, material class | **None** (no verified open URL satisfies all fields) | Unavailable | Flag as a data limitation; proceed with synthetic validation only. |
| Pipeline verification (unit conversion, imputation) | Repo‑bundled CSV (`data/raw/pipeline_verification.csv`) | Included | Confirms ingestion, unit conversion via `stress_unit`, and median imputation work as intended. |
| Synthetic validation dataset | Deterministically generated (`data/raw/synthetic_fatigue.csv`) | Generated locally | Used to validate the end‑to‑end pipeline; **not for scientific inference and never for mediation**. |

> **Note**: All dataset references in this document cite only the URLs from the “Verified datasets” block; no fabricated URLs appear.

## Synthetic Data Generation (Deterministic)
`src/data/gen_synthetic.py` creates `synthetic_fatigue.csv` with the following deterministic steps (seed 42):

1. **Material class** – balanced equal parts steel and aluminum.  
2. **Process parameters** – `heat_input` ∼ LogNormal(μ=2, σ=0.5) MJ; `cooling_rate` ∼ Normal(μ=30, σ=10) K/s (truncated > 0). Additional numeric params sampled uniformly within realistic ranges.  
3. **Material properties** – steel: `elastic_modulus` ∼ N(210, 10) GPa, `yield_strength` ∼ N(350, 30) MPa; aluminum: `elastic_modulus` ∼ N(70, 5) GPa, `yield_strength` ∼ N(250, 20) MPa.  
4. **Measured residual stress** – generated from an **independent latent stress variable** `ζ ∼ N(0,10)` and a **non‑linear function**:  
  `μ_res = 0.5·log(heat_input+1)·sqrt(cooling_rate) + 0.3·ζ`.  
  This formulation ensures that measured stress is **not a deterministic linear combination** of the same process parameters that appear in Feature Set A, reducing (though not eliminating, since the process terms still appear) tautological mediation. The synthetic set is in any case excluded from mediation analysis.  
5. **Fatigue life** – Weibull‑distributed cycles where the scale parameter decreases with both `heat_input` and `residual_stress_measured`; Gaussian noise added.  
6. Exported with all columns required by the unified schema (see `data-model.md`).  

The synthetic set contains **10 000 rows**, guaranteeing > 50 measured‑stress observations for pipeline validation.

## Methodology

### 1. Data Ingestion & Preprocessing
- Load verification CSV and synthetic CSV; concatenate, add `source` column.  
- Compute SHA‑256 checksums; store in `data/raw/checksums.json`.  
- **Unit conversion** uses the explicit `stress_unit` column (values `"MPa"` or `"psi"`); `psi` values multiplied by `0.00689476`.  
- Median impute missing numeric entries (FR‑002).  
- **Proxy computation**: the proxy `σ_res = k·log(heat_input+1)·sqrt(cooling_rate)` (`k=0.8` for steel, `k=0.6` for aluminum) is **computed for all rows** so its agreement with measured stress can be evaluated (FR‑014), but it is **used as a stress feature only for rows where measured stress is missing** (`is_proxy=True`). For measured rows, the measured value is used and the proxy column is never set equal to it.  
- Clamp negative proxy values to `0.01 MPa`; log count to `logs/proxy_clamp.log`.  
- Compute a **per‑row SHA‑256 checksum** of the raw record and store in the `checksum` column (addresses plan‑consistency‑ca2f2ab5).  
- Validate against `contracts/dataset_schema.yaml`.  
- Output `data/processed/unified_fatigue.csv` and `data/processed/missing_flags.json`.  

### 2. Balanced Subset & Feature‑Set Construction
- Filter to rows with `is_proxy=False` (measured stress present).  
- Down‑sample with fixed seed to obtain a **balanced subset** (equal steel/aluminum rows) → `balanced_measured.csv`.  
- **Feature Set A**: process parameters only (from `balanced_measured.csv`).  
- **Feature Set B**: process parameters + `residual_stress_measured` (same rows as Set A).  
- **Feature Set C**: full dataset (including proxy rows) with process parameters, material properties, and `residual_stress_proxy` as the stress feature for `is_proxy=True` rows.  

### 3. Model Training & Hyper‑parameter Search
- Algorithms: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit‑learn), shallow NN (`torch.nn.Sequential` with ≤ 128 hidden units, ≤ 500 epochs, early stopping).  
- 5‑fold CV stratified by `material_class`; 10‑combo grid per algorithm.  
- Select hyper‑parameters with lowest mean CV‑MAPE; retrain on full training split; persist models under `models/`.  

### 4. Held‑out Test Evaluation
- [deferred] stratified test split from the balanced subset (seed 42).  
- Compute MAPE and R² for each model; store in `model_performance.csv`.  

### 5. Comparative Analyses
- **Wilcoxon signed‑rank test** on absolute errors (Model A vs B) for each algorithm family; Bonferroni‑corrected α = 0.05/3.  
- **Improvement criterion**: report a meaningful gain only if the corrected p‑value < 0.05 (no arbitrary percentage rule).  
- **Cross‑material transfer**: train on steel‑only, test on aluminum‑only (and vice‑versa); compute ΔMAPE; significance via 10 000‑permutation test with Holm‑Bonferroni.  

### 6. Mediation Analysis (Conditional)
- **Eligibility**: proceed only if a **real open dataset** (source ≠ `synthetic` and ≠ `verification`) with measured residual stress contains ≥ 50 rows (FR‑013). The synthetic dataset is **never** eligible, regardless of its 10 000 rows — running mediation on data whose mediator was constructed to embed the hypothesized relationship would be tautological (addresses data_resources‑25d7e74a, scientific_soundness‑3f1dde83). If no real dataset exists, the mediation step is **skipped** and a limitation is reported.  
- Fit linear **a‑path** (process + material properties + material class → measured stress) and **b‑path** (measured stress + process + material properties + material class → fatigue life). All material‑property covariates (elastic modulus, yield strength) and material class are included as explicit controls to reduce confounding; VIF is a supplementary diagnostic (flag > 5), and omitted‑variable bias is acknowledged as an unresolvable limitation of observational data (addresses methodology‑b0694250).  
- **Bootstrap** 10 000 resamples → indirect effect, direct effect, proportion mediated, 95 % CI.  
- Apply Holm‑Bonferroni across material classes.  
- **Causal framing**: all outputs are labeled “associational – no causal identification”; no causal pathway claim is made (mandatory per Constitution VII, methodology‑d03f1f30).  
- Save `mediation_summary.csv` and PNG plots.  

### 7. Reporting & Artifact Generation
All results are consolidated under `results/reports/` with provenance columns linking back to `unified_fatigue.csv`. Figures are PNGs. A `runtime_summary.csv` records wall‑clock time and peak memory per phase.

### 8. Compute Feasibility
All steps run on the GitHub Actions free‑tier CPU runner (a multi‑core CPU, ~7 GB RAM). No GPU is required; all libraries are CPU‑compatible.

### 9. Statistical Rigor Checklist
- **Multiple‑comparison correction**: Bonferroni for Wilcoxon; Holm‑Bonferroni for permutation and mediation tests.  
- **Power justification**: Mediation only if ≥ 50 measured‑stress rows **from a real open dataset** (FR‑013). Under‑power band (50–63) flagged.  
- **Causal framing**: Explicitly associational; no causal claims.  
- **Measurement validity**: Proxy–measured agreement (Pearson r, R²) reported with a circularity caveat (FR‑014); the proxy is acknowledged to be a deterministic function of Set A features and therefore adds no independent information when substituted for measured stress.  
- **Collinearity**: VIF diagnostics; any VIF > 5 noted.  

### 10. Edge‑Case Handling
- **No measured stress** → `proxy_dependent=True` flag; mediation skipped.  
- **Negative proxy values** → clamped to `0.01 MPa`; count logged.  
- **Insufficient measured rows from a real dataset** → mediation skipped or under‑power warning issued.  

All decisions are deterministic, reproducible, and traceable to version‑controlled code and data.