# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Dataset Strategy

| Dataset | Role | Verified URL | Format | Key Variables |
|---|---|---|---|---|
| **SILSO Sunspot Number** | Cycle‑boundary reference (external cycle definitions) | `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet` | Parquet | `date`, `sunspot_number` |
| **CMIP6 Solar Forcing (v3.2)** | Independent comparison baseline (never a training target) | `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet` | Parquet | `time`, `solar_forcing` (TSI) |
| **GSN (Group Sunspot Number)** | Primary predictor (1610–present) | **No verified open parquet containing `date` and `gsn` is available**. The closest open parquet does **not** contain the required series. Consequently the pipeline will treat GSN as unavailable and skip any step that requires it, logging `gsn_available = false`. | — | `date`, `gsn` |
| **SORCE/TIM TSI** | Satellite‑era training target (FR‑014) | **No verified open source**; URLs listed under “TSI (jsonl)” in the verified‑datasets block are unrelated. | — | — |
| **2007 Baseline (Wang et al.)** | Baseline for error‑reduction metric (SC‑001) | **No verified open source**; baseline metrics will be omitted. | — | — |

### Critical Dataset‑Variable Fit Check
- **GSN**: Required predictor absent → all model‑training steps become conditional and are skipped; the final report records `gsn_available = false`.
- **SILSO**: Contains `date` and `sunspot_number`; used only for cycle‑boundary detection (no leakage).
- **CMIP6**: Contains `solar_forcing`; used exclusively for validation/comparison (FR‑010/FR‑011).
- **SORCE/TIM & 2007 baseline**: Unavailable → `tsi_available = false`, `baseline_available = false`; downstream steps that depend on them are omitted and reported as `null`.

## 2. Statistical Methodology

### 2.1 Model Selection (conditional)
- **Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_depth=12`, `random_state=42`). Provides fast, CPU‑only non‑linear mapping.
- **Gaussian Process Regressor** (`sklearn.gaussian_process.GaussianProcessRegressor` with RBF kernel). Supplies analytic prediction intervals for uncertainty bands.
- **Cycle‑Agnostic fallback** (GSN‑only Random Forest) – instantiated only if a supervised TSI target exists; otherwise omitted.

### 2.2 Feature Engineering
| Feature | Source | Description |
|---|---|---|
| `gsn` | GSN (if available) | Raw, interpolated, or proxy‑filled value. |
| `cycle_id` (one‑hot) | SILSO cycle definitions | Categorical identifier; satisfies Principle VI. |
| `gsn_lag1` | GSN | One‑month lag to capture inertia. |
| Facular offset | Constant ≈ 0.5 W/m² (documented in `code/config.py`) | Ensures TSI > 0 when GSN ≈ 0 (FR‑012). |

### 2.3 Validation (conditional on TSI)
- **Leave‑One‑Cycle‑Out CV** across all satellite cycles (RMSE, R² per held‑out cycle, bootstrap CI, 1000 iterations).  
- **Hold‑out split (2016‑2020)** to satisfy Constitution Principle VI (training on 2003‑2015, testing on the most recent cycle).  
- **Power disclaimer**: Very few full cycles ⇒ limited statistical power; all metrics report bootstrap confidence intervals.

When TSI is unavailable, all CV and hold‑out metrics are recorded as `null` with explanatory notes.

### 2.4 Multiplicity & Framing
- **Bonferroni correction** for the three pairwise variance tests across Maunder, Dalton, and Modern minima (α/3).  
- **Associational framing**: All statements explicitly note that the analysis is observational (FR‑006).

### 2.5 Cycle Detection
- Apply the SILSO 13‑month smoothed peak detection algorithm; enforce alignment with SILSO‑published cycle maxima within ±6 months (FR‑002). Cycle IDs are derived from external SILSO records (no leakage).

## 3. Gap Handling & Uncertainty

- **Gaps < 1 yr**: Linear interpolation, flagged `quality_flag='interpolated'`.  
- **Gaps ≥ 1 yr**: Fixed low‑activity proxy TSI = 1360.8 W/m² (average of the 2008‑2019 minimum), flagged `quality_flag='proxy'`.  
- **Uncertainty**: GP prediction intervals for reconstruction; bootstrap (exactly 1000 iterations, seed = 42) for variance comparisons of solar minima.

## 4. Compute Constraints

- All steps run on a multi‑core CPU runner. with ≤ 7 GB RAM.  
- No GPU‑only methods are used; therefore no GPU escape hatch is required.

## 5. Limitations & Outlook

Because no open GSN predictor and no open satellite‑era TSI target are available, the core sunspot‑to‑TSI modeling cannot be executed in this version of the pipeline. Consequently, the primary research question—*how the relationship between historical sunspot numbers and TSI varies across cycles*—remains unanswered pending the release of a verified open GSN dataset (or an equivalent proxy) and a verified open satellite‑era TSI record. Future work will integrate such datasets when they become publicly accessible, enabling the full modeling, reconstruction, and validation workflow described in the implementation plan.

---



