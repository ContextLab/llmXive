# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Dataset Strategy

| Dataset | Role | Verified URL | Format | Key Variables |
|---|---|---|---|---|
| **GSN (Group Sunspot Number)** | Primary predictor (1610–present) | **[UNVERIFIED – placeholder]** (no open source currently provides a verified GSN parquet with `date` and `gsn` columns) | — | `date`, `gsn` |
| **SILSO Sunspot Number** | Cycle‑boundary reference (external cycle definitions) | `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet` | Parquet | `date`, `sunspot_number` |
| **CMIP6 Solar Forcing (v3.2)** | Independent comparison baseline only — never a training target | `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet` | Parquet | `time`, `solar_forcing` (TSI) |
| **SORCE/TIM TSI** | Satellite‑era training target (FR‑014) | **No verified open source.** The URLs listed under “TSI/SORCE/TIM” in the verified‑datasets block are unrelated datasets (Ethereum transactions, chat logs, Amazon reviews) and are rejected as dataset‑variable mismatches. Ingestion is optional and skipped. | — | — |
| **2007 Baseline (Wang et al.)** | Baseline for SC‑001 error‑reduction | **No verified open source.** Baseline metrics are optional and omitted. | — | — |

### Critical Dataset‑Variable Fit Check

- **GSN**: Currently no open, verified parquet containing `date` and `gsn` has been identified. Consequently, the pipeline will treat the GSN dataset as unavailable; all steps that require it will be skipped and flagged in the final report. This limitation is recorded in `report.schema.yaml` (`tsi_available = false`).
- **SILSO**: Contains `date` and `sunspot_number`; used solely for external cycle definitions, preventing leakage (spec assumption).
- **CMIP6**: The shard includes a `solar_forcing` variable (verified by inspecting the schema). Used **exclusively** for FR‑010/FR‑011 comparison, never for training (FR‑003 constraint).
- **SORCE/TIM TSI**: Unavailable. **This is a fatal fit issue for FR‑014, SC‑001, and SC‑002** — the pipeline therefore makes all downstream steps that require TSI conditional and logs the omission.
- **2007 baseline**: Unavailable; `rmse_reduction_percentage` and related baseline metrics are optional and omitted.

## 2. Statistical Methodology

### 2.1 Model Selection
- **Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`, `n_estimators=200`, `max_depth=12`, seed pinned): non‑linear, CPU‑fast.
- **Gaussian Process Regressor** (`RBF` kernel): supplies analytic [deferred] prediction intervals for the uncertainty bands (FR‑004).
- **Cycle‑Agnostic fallback** (GSN‑only RF): **not instantiated** when no verified TSI target exists, because any supervised regression still requires a target variable. The pipeline logs this limitation and proceeds without reconstruction.

### 2.2 Feature Engineering
| Feature | Source | Description |
|---|---|---|
| `gsn` | GSN | Group Sunspot Number (gap‑filled, flagged). |
| `cycle_id` (one‑hot) | SILSO cycle definitions | Categorical cycle identifier (Principle VI, FR‑003). |
| `gsn_lag1` | GSN | One‑month lag, captures inertia. |
| facular baseline offset | fixed constant (≈ 0.5 W/m²) | Ensures TSI ≠ 0 when GSN ≈ 0 (FR‑012; internal constant, not persisted). |

### 2.3 Validation
- **Leave‑one‑cycle‑out CV** over satellite‑era cycles (when TSI present): RMSE and R² per held‑out cycle, with bootstrap CIs (≥ 1000 iterations).
- **Hold‑out split (2016‑present)**: when TSI is present, the model is additionally evaluated on the 2016‑2020 period to satisfy Constitution Principle VI (training 2003‑2015). Metrics are reported as `rmse_validation` and `r2_validation`.
- **Power limitation**: very few full cycles → limited power; all metrics carry bootstrap CIs and the limitation is noted in the report.
- When TSI is absent, all CV and hold‑out metrics are recorded as `null` with an explanatory note in `cv_report.json`.

### 2.4 Multiplicity & Framing
- Bonferroni correction for variance tests across the three minima (3 pairwise tests → α/3) (FR‑007).
- All findings labelled associational; no causal claims (FR‑006).

### 2.5 Cycle Detection
- SILSO‑method 13‑month smoothed sunspot‑number peak detection; boundaries must align with known SILSO cycle maxima within ±6 months (FR‑002). Cycle IDs are derived from external SILSO records, not from the GSN series being analyzed (no leakage).

## 3. Gap Handling & Uncertainty

- Gaps < 1 yr: linear interpolation, `quality_flag='interpolated'`.
- Gaps ≥ 1 yr: **fixed low‑activity proxy = 1360.8 W/m²** (average TSI during the 2008‑2019 minimum), `quality_flag='proxy'`; Maunder‑Minimum gaps are flagged but not interpolated.
- Uncertainty: GPR [deferred] prediction intervals for the reconstruction; bootstrap (exactly 1000 iterations, seed pinned) for minima‑variance comparisons.

## 4. Compute Constraints

- 2 vCPU, ~7 GB RAM, ~a few GB disk, CPU‑only; ≤ 6 h runtime excluding downloads (SC‑004, FR‑008).
- All methods (RF, GP, bootstrap, classical stats) have faithful CPU forms — **no GPU escape hatch needed**; no CUDA/bitsandbytes dependencies.

## 5. References & Citations

- SILSO: `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet`
- CMIP6: `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet`

No other URLs are cited; the absence of verified SORCE/TIM and 2007‑baseline sources is stated explicitly rather than papered over.
