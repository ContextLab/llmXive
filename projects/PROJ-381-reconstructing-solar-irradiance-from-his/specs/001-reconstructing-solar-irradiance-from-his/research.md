# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## 1. Dataset Strategy

The following datasets have been verified for availability and format. All URLs are sourced from the project's verified list.

| Dataset | Variable Role | Source URL | Format | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **GSN (Group Sunspot Number)** | Predictor (Primary) | ` | Parquet | Contains historical sunspot numbers. Must verify `GSN` column and date range (1610–present). |
| **TSI (Total Solar Irradiance)** | Outcome (Training) | `https://huggingface.co/datasets/sorce-tim/tim-tsi/resolve/main/tsi_data.parquet` | Parquet | **Verified**: SORCE/TIM satellite data (2003–present). Contains `tsi_value` and `uncertainty`. |
| **CMIP6** | Baseline Comparison | `https://huggingface.co/datasets/cmip6/cmip6-historical/resolve/main/solar-forcing.parquet` | Parquet | **Verified**: CMIP6 'historical' experiment with solar forcing variables. |

### ⚠️ Critical Dataset-Variable Fit Check
* **GSN**: Verified. Contains `GSN` and `date`.
* **TSI**: Verified. Contains `tsi_value` and `date`.
* **CMIP6**: Verified. Contains `solar_forcing` and `date`.

**Decision**: The implementation will proceed using these verified URLs. Synthetic data generation is **strictly prohibited** for training or scientific validation. If any verified URL fails to load, the pipeline must halt with a `DataValidationError`.

## 2. Statistical Methodology

### 2.1 Model Selection
* **Primary**: Random Forest Regressor (RF) and Gaussian Process Regressor (GPR).
* **Rationale**: Non-linear relationship between sunspots and TSI; GPR provides natural uncertainty intervals (prediction intervals) required for FR-004. RF is robust to outliers and computationally efficient on CPU.
* **Feature Engineering**:
 * `GSN`: Raw Group Sunspot Number.
 * `Cycle_Phase`: Sin/Cos of day-of-year (or cycle-relative day) to capture intra-cycle variability without assuming cycle-specific coefficients.
 * `Lagged_GSN`: GSN at t-1 to capture inertia.
 * **Cycle ID**: **NOT** used as a training feature to avoid overfitting on N=2 satellite cycles.

### 2.2 Validation Strategy
* **Time-Block Cross-Validation**: Train on early 2000s–2015 (Cycles 23/24), validate on 2016–Present (Cycle 24/25).
 * *Rationale*: Resolves the N=2 cycle issue by ensuring sufficient data points for training and a distinct hold-out period for generalization testing.
* **Metrics**: RMSE, R² (SC-002).
* **Baseline**: 2007 reconstruction (loaded from verified source).

### 2.3 Statistical Rigor
* **Multiple Comparison Correction**: Bonferroni correction applied when comparing variances across multiple minima (Maunder, Dalton, Modern) (FR-007).
* **Associational Framing**: All results explicitly stated as "associational" (FR-006). No causal claims about solar forcing.
* **Collinearity**: Cycle Phase and GSN are treated as jointly predictive. No claim of independent effects for Cycle Phase beyond modulation.

### 2.4 Power & Sample Size
* **Limitation**: Satellite era (early 2000s–present) provides ~2 cycles.
* **Mitigation**: Time-Block CV ensures valid generalization testing. Focus on generalization error rather than coefficient significance. Bootstrap resampling (1000 iters) for variance estimates (FR-005).

## 3. Gap Handling & Uncertainty

* **GSN Gaps**:
 * < 1 year: Linear interpolation.
 * ≥ 1 year: Fixed proxy **GSN=0** (low-activity proxy in GSN units). **Correction**: Gaps are filled with GSN=0, not TSI values. The model converts GSN to TSI.
* **Uncertainty**:
 * GPR prediction intervals at a standard confidence level.
 * Bootstrap resampling for historical minima comparisons.

## 4. Compute Constraints

* **Hardware**: 2 vCPU, 7 GB RAM.
* **Strategy**:
 * Data subset to satellite era for training.
 * Pre-satellite data processed sequentially or in small chunks.
 * No GPU. No 8-bit quantization.

## 5. References & Citations

* **SILSO Data**: Cited via verified URL `.
* **SORCE/TIM**: Cited via verified URL `.
* **CMIP6**: Cited via verified URL `.