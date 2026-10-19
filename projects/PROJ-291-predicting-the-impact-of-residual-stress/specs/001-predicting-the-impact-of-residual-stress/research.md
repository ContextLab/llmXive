# Research: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

## Overview
We aim to answer:

*“To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?”*

**Verified data availability finding**: No verified open dataset provides measured residual stress together with fatigue life, process parameters, and material class. The previously considered NIST and UCI sources were verified as **unrelated to materials engineering** (a doctor–patient conversation corpus and a Human Activity Recognition dataset respectively) and are excluded. Consequently:

1. FR-001's requirement to ingest data from NIST/UCI/OpenML repositories is **partially unmet** — the schema-unification, parsing, unit-standardization, and imputation machinery is implemented and tested against the repo-bundled verification CSV, but no verified suitable repository source exists. This is a **spec-root gap flagged for kickback** (FR-001 and US-1 should be revised).
2. The pipeline relies on a **synthetic validation dataset** (`data/raw/synthetic_fatigue.csv`) containing all required fields, generated deterministically from a pinned seed.
3. **The research question cannot be answered with real measured residual stress from open data.** All conclusions depending on measured stress are based on the synthetic dataset and are labeled "synthetic validation — pipeline validation only, not an external scientific claim". This is stated as an explicit scope limitation rather than papered over.

## Dataset Strategy
| Requirement | Source | Availability | Action |
|-------------|--------|--------------|--------|
| Primary dataset with fatigue life, process parameters, **measured** residual stress, and material class | **None** (no verified open URL contains all four; NIST/UCI candidates verified as unrelated) | Unavailable | Use the **synthetic validation dataset** (`data/raw/synthetic_fatigue.csv`) generated programmatically (see “Synthetic Data Generation”). Results are labeled "synthetic validation" and are **not** used for external scientific claims. |
| Pipeline verification (parsing, unit conversion, imputation) | Repo-bundled minimal CSV (`data/raw/pipeline_verification.csv`) with realistic ranges of `heat_input`, `cooling_rate`, mixed MPa/psi stress values, and deliberately missing entries | Included in repo | Confirms ingestion, unit conversion, and median imputation work as intended. |
| NIST / UCI / OpenML repository data | **No verified suitable source exists** (verified candidates are unrelated to materials engineering) | Unavailable | Omitted. FR-001 repository-ingestion requirement flagged as a spec-root gap for kickback; no unrelated dataset is substituted. |

> **Planned limitation**: The mediation analysis requires measured residual stress. The lack of such data in open sources is a *planned limitation*, not a silent failure. All statements about mediation are clearly marked as based on the synthetic dataset, associational, and pipeline-validation-only.

## Synthetic Data Generation
The synthetic validation dataset is created deterministically from a seed (`SEED=42`) to ensure reproducibility:

1. **Material Class**: Randomly assign “steel” or “aluminum” (balanced 50/50).
2. **Process Parameters**: Sample `heat_input` (MJ) from a log-normal distribution (μ=2, σ=0.5) and `cooling_rate` (K/s) from a normal distribution (μ=30, σ=10), truncated to positive values. Additional numeric parameters are drawn from uniform ranges appropriate for typical manufacturing processes.
3. **Material Properties**: For steel, draw `elastic_modulus` ~ N(210, 10) GPa and `yield_strength` ~ N(350, 30) MPa; for aluminum, draw `elastic_modulus` ~ N(70, 5) GPa and `yield_strength` ~ N(250, 20) MPa.
4. **Measured Residual Stress**: Generate `residual_stress_measured` by sampling from a normal distribution whose mean depends on `heat_input` and `cooling_rate` through a **deliberately different stochastic functional form** (e.g., μ = 0.7·heat_input + 0.3·cooling_rate, i.e., an additive — not multiplicative — relation) plus substantial Gaussian noise (σ = 5 MPa). This process is **independent of the proxy formula** `σ_res = k·heat_input·cooling_rate` (different functional form, additive rather than multiplicative, noise-driven), so no tautology exists between the mediator and the predictors. The mediation result on this dataset is therefore not guaranteed by construction — but it is also **not a real-world measurement**, which is why all such results are labeled pipeline-validation-only.
5. **Fatigue Life**: Simulate `fatigue_life_cycles` using a Weibull model where the scale parameter is a decreasing function of both `heat_input` and `residual_stress_measured`, plus random noise.
6. **Export**: Save as CSV with the columns required by the unified schema (see `data-model.md`).

The synthetic dataset contains **10 000 rows**, guaranteeing > 50 measured-stress observations.

## Methodology

### 1. Data Ingestion & Preprocessing
- **Load** the repo-bundled verification CSV and the synthetic dataset; checksum each raw file (SHA-256) and store under `data/raw/`; embed the checksum as a `checksum` column in the unified CSV for provenance. No external repository download is performed (see Dataset Strategy).
- **Unit Standardization**: Convert any stress values to MPa (`1 psi = 0.00689476 MPa`).
- **Missing-Value Imputation**: Median imputation per numeric column (FR-002).
- **Proxy Residual Stress**: Compute `σ_res = k·heat_input·cooling_rate` **for all rows** (`k=0.8` for steel, `k=0.6` for aluminum), independently of whether a measured value exists — this guarantees rows with both measured and proxy values exist, making the FR-014 agreement computation feasible. Set `is_proxy=True` for rows where the proxy replaces a missing measured value; otherwise `is_proxy=False`. Clamp negative proxy values to 0.01 MPa and log adjustments.
- **Proxy–Measured Agreement (FR-014)**: Compute Pearson's r and R² between proxy and measured stress on rows where both exist. **Explicit caveat**: the proxy is a deterministic function of the same process parameters used as predictors, so this is a **descriptive agreement check, not an independent validation** — the comparison is inherently circular. The metrics are reported alongside a bias-and-limitations discussion, per FR-014; no external reference exists.
- **Contract Validation**: Validate the processed CSV against `contracts/dataset_schema.yaml`; abort on failure.
- **Reproducibility**: Random seed `SEED=42` used for all stochastic operations (FR-010).

### 2. Feature-Set Construction (Balanced Subsets)
| Feature Set | Columns (post‑processing) | Sample Selection |
|-------------|---------------------------|------------------|
| **A – Process‑only** | `heat_input`, `cooling_rate`, `other_process_params` | All rows with measured stress (`is_proxy=False`) — balanced subset |
| **B – Process + Measured Stress** | A + `residual_stress_measured` | **Identical balanced subset as A** (equal sample size, so paired comparisons isolate the stress feature's contribution) |
| **C – Process + Material Props + Proxy Stress** | A + `material_class`, `elastic_modulus`, `yield_strength`, `residual_stress_proxy` | Full dataset (includes proxy rows, per FR-012); **never compared head-to-head with A/B via paired tests** — reported descriptively with explicit sample-size disclosure |

### 3. Model Training & Evaluation
- **Algorithms**: `RandomForestRegressor`, `GradientBoostingRegressor` (scikit-learn), shallow feed-forward NN (`torch.nn.Sequential` with one hidden layer ≤ 128 units, early stopping ≤ 500 epochs).
- **Hyper-parameter Grid**: 10 combos per algorithm.
- **5-fold CV**: Stratified by `material_class`; same seed across folds. Record MAPE and R² per fold.
- **Model Selection**: Choose hyper-parameters with lowest mean CV-MAPE. Retrain on the full training split.
- **Held-out Test Set**: Stratified by material, seed 42. Compute final MAPE and R².

### 4. Comparative Analyses
- **Wilcoxon Signed-Rank Test** (non-parametric, per FR-008; no paired t-test is used): Compute absolute errors for Model A vs. Model B **only on the measured-stress subset** (`is_proxy=False`), on identical rows. Run Wilcoxon per algorithm family and apply **Bonferroni correction** (α = 0.05/3).
- **Improvement Threshold (Principle VII)**: Report a stress-mediated model as meaningfully better only if its MAPE is **≥10 % lower** than the baseline, demonstrated on the held-out test set together with the paired Wilcoxon result.
- **Cross-Material Transfer**: Train on steel-only, test on aluminum-only, and vice-versa; compute ΔMAPE relative to within-material baseline. Significance assessed via **permutation test** (10 000 permutations, α = 0.05, Holm-Bonferroni).

### 5. Mediation Analysis (Conditional, Associational Framing)
- **Eligibility Check**: Proceed only if rows with `is_proxy=False` ≥ 50 (the operational threshold mandated by FR-013, whose a-priori power analysis requires ≈45 for f²=0.15, α=0.05, power=0.80). If the count falls in the **50–63 under-power band**, the report flags the mediation estimate as potentially under-powered (elevated Type II error risk, unstable indirect-effect estimates) and widens the interpretation caveat. If < 50, log a warning and skip.
- **Model Specification**: Linear models for the **a-path** (process → residual stress) and **b-path** (residual stress → fatigue life) controlling for `heat_input`, `cooling_rate`, `elastic_modulus`, `yield_strength`, `material_class`, and any additional numeric process parameters.
- **Collinearity Diagnostic**: Compute Variance Inflation Factor (VIF) for each predictor; flag any > 5.
- **Bootstrap**: 10 000 resamples.
- **Multiple-Comparison**: Holm-Bonferroni correction across material classes.
- **Causal Framing (mandatory)**: The data are observational/synthetic with **no causal identification strategy** (no randomization, no instruments). Mediation inherently assumes a causal pathway that these data cannot license; therefore all indirect-effect results are reported strictly as **associational** and labeled "associational — no causal identification" in every table and figure. No causal interpretation is offered.
- **Synthetic-data caveat**: When mediation runs on the synthetic dataset, outputs are additionally labeled "pipeline validation only — synthetic data, not an external scientific claim". The research question cannot be answered without independently measured residual stress; this scope limitation is stated in the final report and flagged for spec kickback.
- **Outputs**: `mediation_summary.csv` (indirect effect, direct effect, proportion mediated, 95 % CI, associational and synthetic-data labels) and PNG effect-size plots. (FR-006, FR-007, SC-001, SC-003.)

### 6. Reporting
All results are stored under `results/reports/`:
- Model metrics: `model_performance.csv`
- Wilcoxon test: `wilcoxon_test.csv`
- Cross-material ΔMAPE: `cross_material.csv`
- Proxy–measured agreement (descriptive, circularity caveat): `proxy_agreement.csv`
- Mediation (if executed): `mediation_summary.csv`
- Figures (PNG): `*.png`

Each table/figure includes a provenance column linking back to the originating row(s) in `data/processed/unified_fatigue.csv`.

### 7. Compute Feasibility
- **CPU-only** implementation; total runtime on a fresh GitHub Actions runner ≤ 2.5 h, RAM peak ≤ 6 GB, disk ≤ 12 GB.
- No GPU resources required; all libraries are compatible with the runner’s environment.

### 8. Statistical Rigor
- **Multiple-Comparison**: Bonferroni for Wilcoxon tests; Holm-Bonferroni for mediation and permutation tests.
- **Power Consideration**: Mediation performed only when ≥ 50 measured-stress rows exist (FR-013 threshold); the 50–63 band is explicitly flagged as potentially under-powered, with elevated Type II error risk noted.
- **Causal Framing**: All mediation results are explicitly labeled *associational — no causal identification*.
- **Measurement Validity**: No external validation dataset for the proxy exists; the proxy–measured agreement check is reported descriptively with an explicit circularity caveat (the proxy is a deterministic function of the predictor process parameters). Synthetic measured stress is generated by a stochastic model deliberately independent of the proxy formula.
- **Collinearity**: VIF diagnostics are reported; VIF > 5 triggers a caution note.

### 9. Edge-Case Handling
- **No measured residual stress** → analysis proceeds with Feature C only; final report includes flag `proxy_dependent=True` and omits mediation.
- **Sample size < 50** → mediation step skipped with logged warning; **50–63** → mediation runs with an under-power warning.
- **Negative proxy values** → clamped to 0.01 MPa; adjustment logged.

All decisions are deterministic, reproducible, and fully traceable to the code and data versions recorded in the project state file.