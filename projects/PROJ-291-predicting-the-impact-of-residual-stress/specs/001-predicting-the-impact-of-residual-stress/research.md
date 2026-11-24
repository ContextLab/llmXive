# Research: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

## Overview
**Research Question**  
*To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?*

### Scope Statement
Publicly available fatigue datasets that contain **measured residual stress**, process parameters, material‑property attributes, and fatigue life are currently **unavailable** (no verified open URL satisfies all fields). Consequently:

1. **Predictive‑gain analysis** (baseline vs. stress‑mediated models) will be performed **only on a deterministic synthetic dataset** (generated with seed 42) **as a methodological illustration**. No empirical claims about real-world predictive improvement will be made.  
2. **Mediation analysis** will be **performed only when a real open dataset provides ≥ 50 rows with measured residual stress** (fulfilling FR‑013). If this condition is not met, mediation is **skipped** and a log entry records the limitation. No synthetic mediation will be executed to avoid violating the power requirement.  
3. All results derived from synthetic data are **explicitly labeled “illustrative – not empirical”** and are **not used to support scientific conclusions**.

### Spec Deviation Note
FR‑003 mandates a **linear** proxy `σ_res = k·heat_input·cooling_rate`. The plan implements exactly this linear form (k = 0.8 for steel, k = 0.6 for aluminum). Any prior non‑linear formulation has been removed.

## Dataset Strategy
| Requirement | Source | Availability | Action |
|-------------|--------|--------------|--------|
| Primary open dataset with fatigue life, process parameters, **measured** residual stress, material class | **None** (no verified open URL satisfies all fields) | Unavailable | Flag as a data limitation; predictive‑gain analysis proceeds only on synthetic data for illustration. |
| Pipeline verification (unit conversion, imputation) | Repo‑bundled CSV (`data/raw/pipeline_verification.csv`) | Included in repository | Confirms ingestion, unit conversion via `stress_unit`, and median imputation work as intended. |
| Synthetic validation dataset | Deterministically generated (`data/raw/synthetic_fatigue.csv`) | Generated locally (seed 42) | Used to validate the end‑to‑end pipeline; **never for scientific inference** and **never for mediation** unless explicitly marked illustrative. |

All dataset references cite only the URLs listed in the “Verified datasets” block of the user message; no fabricated URLs are introduced.

## Methodology

### 1. Data Ingestion & Preprocessing
- Load verification CSV and synthetic CSV; concatenate and add a `source` column.  
- Compute SHA‑256 checksums for each raw file; store in `data/raw/checksums.json`.  
- **Unit conversion** uses the explicit `stress_unit` column (`MPa` or `psi`). `psi` values multiplied by `0.00689476`.  
- Median‑impute missing numeric entries (FR‑002).  
- **Linear proxy computation**: `σ_res = k·heat_input·cooling_rate` (`k=0.8` for steel, `k=0.6` for aluminum). Computed for **all rows** so that FR‑014 (proxy–measured agreement) can be evaluated, but the proxy is **used as the stress feature only when `residual_stress_measured` is missing** (`is_proxy=True`).  
- Clamp negative proxy values to `0.01 MPa`; log the count.  
- Record per‑row SHA‑256 checksum in `checksum` column (data‑provenance).  
- Validate against `contracts/dataset_schema.yaml`; abort on failure.  
- Output `data/processed/unified_fatigue.csv` and `data/processed/missing_flags.json`.

### 2. Balanced Subset & Feature‑Set Construction
- Filter to rows with `is_proxy=False` (measured stress present).  
- Down‑sample with fixed seed to obtain a **balanced steel/aluminum subset** → `balanced_measured.csv`.  
- **Feature Set A**: process parameters only (from balanced subset).  
- **Feature Set B**: process parameters + `residual_stress_measured` (same rows as Set A).  
- **Feature Set C**: full dataset (including proxy rows) with process parameters, material properties, and `residual_stress_proxy` as the stress feature for `is_proxy=True` rows.

### 3. Model Training & Hyper‑parameter Search
- Algorithms: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit‑learn), shallow NN (`torch.nn.Sequential` with ≤ 128 hidden units, ≤ 500 epochs, early stopping).  
- 5‑fold CV stratified by `material_class`; 10‑combo grid per algorithm.  
- Select hyper‑parameters with lowest mean CV‑MAPE; retrain on full training split; persist models under `models/<feature_set>/<algorithm>.pt`.

### 4. Held‑out Test Evaluation
- Stratified train/test split from the balanced subset (seed 42).  
- Compute MAPE and R² for each model; store in `results/reports/model_performance.csv`.

### 5. Comparative Statistics (Illustrative)
- **Paired t‑test** on absolute errors (Model A vs B) for each algorithm family **and** **Wilcoxon signed‑rank test** as a non‑parametric backup.  
- Apply **Bonferroni correction** (α = 0.05/3).  
- **Improvement thresholds** (≥10 % lower MAPE for Model B vs A) are reported **only as illustrative criteria**; no empirical claim is made unless a real dataset later becomes available (Constitution Principle VII).  
- **Cross‑material transfer**: train on steel‑only, test on aluminum‑only (and vice‑versa); compute ΔMAPE; significance via 10 000‑permutation test with Holm‑Bonferroni.

### 6. Mediation Analysis (Conditional – **Not a Primary Claim**)
- **Eligibility**: If a **real open dataset** (source ≠ `synthetic` ∧ source ≠ `verification`) contains ≥ 50 rows with measured residual stress, perform mediation on that real data (satisfying FR‑013).  
- **Otherwise**: Mediation is **skipped**; a log entry notes “Insufficient measured‑stress rows – mediation omitted”. No synthetic mediation is run.  
- When eligible, fit linear **a‑path** (process + material properties + material class → measured stress) and **b‑path** (measured stress + process + material properties + material class → fatigue life). Include VIF diagnostics (flag > 5).  
- **Bootstrap** 10 000 resamples → indirect effect, direct effect, proportion mediated, 95 % CI.  
- Apply Holm‑Bonferroni across material classes.  
- **Causal framing**: all outputs labeled “associational – no causal identification”.  
- Save `mediation_summary.csv` and PNG plots **only when real data qualify**.

### 7. Reporting & Artifact Generation
All results are consolidated under `results/reports/` with provenance columns linking back to `unified_fatigue.csv`. Figures are PNGs. A `runtime_summary.csv` records wall‑clock time and peak memory per phase.

### 8. Compute Feasibility
All steps run on the GitHub Actions free‑tier CPU runner (≈ 2.5 h, < 7 GB RAM). No GPU is required; all libraries are CPU‑compatible.

### 9. Statistical Rigor Checklist
- **Multiple‑comparison correction**: Bonferroni for t‑/Wilcoxon tests; Holm‑Bonferroni for permutation and mediation tests.  
- **Power justification**: Mediation only if ≥ 50 measured‑stress rows from a real dataset (FR‑013). Synthetic data is **not** counted toward this requirement.  
- **Causal framing**: Explicitly associational; no causal claims.  
- **Measurement validity**: Proxy–measured agreement (Pearson r, R²) reported when both exist (FR‑014).  
- **Collinearity**: VIF diagnostics; any VIF > 5 noted.

### 10. Edge‑Case Handling
- **No measured stress** → `is_proxy=True` for all rows; mediation skipped; models use proxy where required.  
- **Negative proxy values** → clamped to `0.01 MPa`; count logged.  
- **Insufficient measured rows** → mediation omitted with warning; predictive‑gain illustration proceeds on synthetic data.

All decisions are deterministic, reproducible, and traceable to version‑controlled code and data.
