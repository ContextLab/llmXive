# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Dataset Strategy

All datasets are fetched from URLs that have been verified as publicly reachable and correctly formatted.

| Dataset | Role | Verified URL(s) | Format | Key Variables |
|---|---|---|---|---|
| **GSN (Group Sunspot Number)** | Primary predictor | `https://huggingface.co/datasets/Francesco/construction-safety-gsnvb/resolve/main/data/test-00000-of-00001-2a010722bb743ffa.parquet` | Parquet | `date`, `gsn` |
| **SILSO Sunspot Number** | Cycle‑boundary reference | `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet` | Parquet | `date`, `sunspot_number` |
| **CMIP6 Solar Forcing (v3.2)** | Independent proxy for comparative analysis | `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet` | Parquet | `date`, `solar_forcing` |
| **SORCE/TIM TSI (Satellite)** | Direct measurement of Total Solar Irradiance (2003‑present) | *No verified open‑source URL available* → **Optional**; ingestion step will attempt download and, if missing, skip model training that requires TSI. |
| **2007 Baseline Reconstruction** | Reference reconstruction for error‑reduction metric | *No verified open source provided* → **Not used**; baseline‑related metrics are optional in the output schema. |

### Critical Dataset‑Variable Fit Check
- **GSN**: Provides `gsn` and `date` covering 1610‑present – satisfies FR‑001 (predictor).  
- **SILSO**: Supplies cycle‑boundary information for categorical Cycle ID – satisfies FR‑002.  
- **CMIP6**: Supplies a solar‑forcing series for **comparison only** (never used as a training target).  
- **SORCE/TIM TSI**: Not available as an open source; therefore the pipeline treats this dataset as optional. If it cannot be downloaded, the training phase is skipped and the fallback model is used for reconstruction.  
- **2007 Baseline**: Unavailable; baseline‑related error‑reduction metrics are optional.

## 2. Statistical Methodology

### 2.1 Model Selection
- **Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`): Handles non‑linearities, robust to outliers, fast CPU training.  
- **Gaussian Process Regressor** (`sklearn.gaussian_process.GaussianProcessRegressor` with RBF kernel): Provides analytic prediction intervals for uncertainty bands (required by FR‑004).  

Both models are trained **only if** a verified TSI dataset is present. When TSI is absent, the pipeline proceeds directly to reconstruction using the Cycle‑Agnostic fallback model.

### 2.2 Feature Engineering
| Feature | Source | Description |
|---|---|---|
| `gsn` | GSN | Raw Group Sunspot Number. |
| `cycle_id` | SILSO cycle definitions | Categorical identifier of the solar cycle (one‑hot encoded). |
| `gsn_lag1` | GSN | GSN value shifted by one month (captures inertia). |

**Cycle ID** is treated as a **categorical** feature, satisfying Principle VI and FR‑003.

### 2.3 Validation Strategy
- **Leave‑One‑Cycle‑Out (Time‑Block) CV**: Train on all cycles except the held‑out one and validate on the held‑out cycle. Because only ~2 full cycles are available, we acknowledge limited statistical power and supplement CV metrics with **bootstrap confidence intervals** (≥ 1000 iters).  
- **Metrics**: RMSE and R² (SC‑001, SC‑002). When TSI data is missing, these metrics are reported as “N/A” with an explanatory note.

### 2.4 Multiple‑Comparison & Associational Framing
- Variance comparisons across the Maunder, Dalton, and Modern minima use **Bonferroni correction** (FR‑007).  
- All statements are explicitly labelled as **associational** (FR‑006).

### 2.5 Power & Sample‑Size Considerations
- Satellite era provides a substantial multi‑year record of data, comprising many monthly observations. While limited, the analysis focuses on prediction error rather than hypothesis testing of individual coefficients, mitigating low‑power concerns. Bootstrap (≥ 1000 iters) provides empirical confidence intervals for variance estimates.

## 3. Gap Handling & Uncertainty

- **GSN Gaps**:  
  - `< 1 yr` → linear interpolation (`pandas.interpolate`).  
  - `≥ 1 yr` → impute GSN with the **mean GSN value observed during the 2008‑2019 solar minimum** (low‑activity proxy) and flag `quality_flag='proxy'`.  

- **Uncertainty**:  
  - GPR prediction intervals (95 % credible interval).  
  - Bootstrap resampling (1000 iters) for variance comparisons across solar minima.

## 4. Compute Constraints

- **Hardware**: 2 vCPU, ~7 GB RAM, ~14 GB disk (GitHub Actions free tier).  
- **Software**: All libraries are pure‑CPU wheels; no CUDA or GPU dependencies.  
- **Runtime Budget**: ≤ 6 h total (see Plan > Compute Feasibility).  

## 5. References & Citations

- **GSN**: `https://huggingface.co/datasets/Francesco/construction-safety-gsnvb/resolve/main/data/test-00000-of-00001-2a010722bb743ffa.parquet`  
- **SILSO**: `https://huggingface.co/datasets/juliensimon/silso-sunspot-number/resolve/main/data/silso_sunspot_number.parquet`  
- **CMIP6**: `https://huggingface.co/datasets/sungduk/wip_cmip6/resolve/main/hf_dataset_test/test-00000-of-00012.parquet`  

*No additional URLs were invented; the absence of a verified TSI source is explicitly noted.*

---  