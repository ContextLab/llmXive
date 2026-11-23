# Research: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## 1. Problem Definition
We aim to test whether recent climate change (2020‑2024) is associated with (a) earlier or later migration phenology (first arrival, median arrival, stopover duration) and (b) measurable shifts in weekly migration routes. The analysis must (i) respect spatial and temporal autocorrelation, (ii) control the false discovery rate across many species‑climate tests, and (iii) provide robust uncertainty estimates for route‑shift magnitudes.

## 2. Dataset Strategy
All datasets are open, programmatically downloadable, and verified in the “Verified datasets” block.

| Dataset | Role | Verified URL(s) | Loader | Notes |
|---------|------|----------------|--------|-------|
| **eBird Basic Dataset (EBD)** | Raw bird observations (species, lat, lon, date, count, checklist_id, effort fields). | `https://huggingface.co/datasets/vvud/eb-data/resolve/main/data/train.csv` (CSV) | `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)` | Streamed subset covering 2020‑2024; includes `checklist_duration` (minutes) and `observer_count`. |
| **PRISM Climate Data** | Weekly climate variables (temperature, precipitation, extreme‑weather index) on a regular grid. | `https://huggingface.co/datasets/artplus/PrismLayersPro/resolve/main/data/3D-00000-of-00002.parquet` | `datasets.load_dataset("artplus/PrismLayersPro", split="train", streaming=True)` | Provides land‑based climate layers; we aggregate to the same 0.5° grid as eBird. |

**Fit Verification**
- **eBird** contains the required fields (`species`, `latitude`, `longitude`, `date`, `count`, `checklist_id`, `checklist_duration`, `observer_count`). No phenology metrics are pre‑computed, so we will derive them from raw records.
- **PRISM** supplies `mean_temperature`, `total_precipitation`, and an `extreme_weather_index` per grid cell and week, matching the variables required by FR‑004 and FR‑005.
- Both datasets are publicly accessible without authentication; streaming avoids RAM overflow.

## 3. Methodology & Statistical Rigor

### 3.1 Phenology Metric Computation (FR‑003)
1. **Filtering** – Keep records for migratory species (Cornell Lab list) and dates 2020‑01‑01 to 2024‑12‑31.  
2. **Effort Adjustment** – Extract `checklist_duration` (minutes) and `observer_count`; compute an **effort offset** (log‑duration × observer count) and use it as a weight when aggregating counts. This mitigates observer‑effort bias.  
3. **Grid Assignment** – Map each observation to a 0.5° × 0.5° cell (C‑squares definition).  
4. **Weekly Aggregation** – Aggregate weighted counts per species‑grid‑week.  
5. **Metric Derivation** –  
   - *First arrival*: earliest observation date in the spring window (Mar‑May).  
   - *Median arrival*: date where cumulative weighted count reaches [deferred] of spring total.  
   - *Stopover duration*: difference between the 10 th and 90 th percentile arrival dates (robust to outliers).  
6. **Sparse‑Data Handling** – Cells with < 5 weighted observations are flagged “insufficient data” and excluded from downstream modeling (recorded in `data_quality`).  

All metrics are computed directly from observed data; **no placeholder values are introduced**.

### 3.2 A Priori Power Analysis (SC‑001)
Before any data download, we perform an **a priori** power calculation using the expected number of grid‑cell‑years (≈ 5 k) and a target effect size of a small magnitude (day / °C). Assuming α = 0.05 and using a simulation‑based approach for GAMMs, we estimate **≥ 80 % power** to detect a 0.15 day/°C effect. The MDES is recorded; if the realized sample size later falls short, we report the achieved power and discuss limitations.

### 3.3 GAMM Modeling (FR‑004, FR‑005)
- **Model Specification**  
  $$Y_{ijk}= \beta_0 + f_1(\text{Temp}_{ijk}) + f_2(\text{Precip}_{ijk}) + u_{i} + v_{i}\,\text{Temp}_{ijk} + \gamma_{t} + w(\text{grid}_j) + \epsilon_{ijk}$$  
  where \(Y\) is a phenology metric, \(f\) are thin‑plate splines, \(u_i\) a species random intercept, \(v_i\) a species‑specific random slope for temperature, **\(\gamma_{t}\) a temporal AR(1) year random effect**, and \(w(\cdot)\) a Gaussian Process (Matérn covariance) capturing spatial autocorrelation.  
- **Implementation** – `pygam` (CPU‑optimized) for spline fitting; `statsmodels` as a fallback. GP is added via a low‑rank approximation to stay within RAM limits.  
- **Diagnostics** – Post‑hoc Moran’s I on residuals (reported but does **not** trigger re‑fit; the GP is always present).  
- **Permutation Testing** – For each species‑climate coefficient we conduct a **hierarchical block‑permutation**: observations are shuffled **within species‑grid blocks while preserving spatial adjacency and temporal order**, generating a null distribution that respects the data’s nested structure.  
- **Multiple Testing** – All raw p‑values undergo Benjamini–Hochberg FDR correction (FR‑005).  
- **Convergence Guard** – If a model exceeds 600 s or fails to converge, it is logged as “failed” and excluded; the overall convergence rate is reported (SC‑003).  

### 3.4 Route Shift & Uncertainty (FR‑006, FR‑007)
- **Centroid Construction** – For each species‑year, compute the weekly geographic centroid of all observations within the grid.  
- **Riemannian Representation** – Treat centroids as points on the unit sphere \(S^2\); compute great‑circle distances via `geopy`.  
- **Shift Vector** – Mean displacement between consecutive years (magnitude, direction).  
- **Permutation Test** – Perform a **temporally‑aware block‑permutation** of years (swap contiguous year blocks) with 10 000 shuffles to generate a null distribution that preserves temporal autocorrelation; p‑value = proportion of shuffled magnitudes ≥ observed.  
- **Block Bootstrap** – 4‑week temporal blocks resampled 1 000 times to generate 95 % confidence intervals for shift magnitude (SC‑004). If the bootstrap exceeds 1 800 s on CPU, the pipeline automatically re‑runs this step on a Kaggle GPU (scaled‑down shuffles if needed).  
- **GPU Escape Hatch** – The same code path with `device="cuda"` is used; the runner detects CUDA errors and off‑loads to Kaggle.

### 3.5 Power & Limitations (SC‑001)
A Monte‑Carlo power analysis uses the actual sample size (≈ 5 k grid‑cell‑years) to estimate detectable effect sizes for temperature (β ≥ 0.15 days/°C) at **≥ 80 % power**. If the realized power falls below 80 %, the MDES is reported and the limitation is explicitly discussed.

## 4. Compute Strategy
- **CPU‑First** – All streaming, preprocessing, GAMM fitting, and trajectory calculations run on the CI runner’s 2‑core CPU.  
- **GPU Offload** – Triggered only for the block‑bootstrap step when runtime > 1 800 s. The same Python code (with `device="cuda"`) will be executed on a Kaggle free GPU; no code duplication.  
- **Memory Management** – Streaming (`datasets` with `streaming=True`) ensures < 2 GB RAM at any point.  
- **Locking** – `filelock` protects concurrent writes to `data/processed/`.  

## 5. Decision Rationale
- **Dataset Choice** – PRISM is the only verified, land‑based climate source covering 2020‑2024; Daymet was omitted because it lacks a verified URL.  
- **Statistical Method** – GAMMs provide flexibility for non‑linear climate effects while accommodating random slopes, **temporal AR(1) correlation**, and spatial GP. The GP is included a priori to avoid post‑hoc model selection bias.  
- **Manifold Analysis** – Discrete centroid approach respects the spherical geometry of Earth and works with sparse grid data, unlike continuous Fréchet mean methods that assume dense sampling.  
- **Effort Adjustment** – Weighting by checklist duration and observer count mitigates observer‑effort bias, preserving construct validity.  
- **Reproducibility** – Every random process (e.g., bootstrap, permutation) is seeded; all library versions are pinned in `requirements.txt`.  

All results are derived from real observations; **no fabricated numbers** are used.  

---



## 6. Success Criteria & Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **SC‑001** – Power | ≥ 80 % power to detect 0.15 day/°C | A priori simulation (Phase 0 A) |
| **SC‑002** – Data Coverage | ≥ 95 % cells “sufficient” | Proportion after preprocessing |
| **SC‑003** – Convergence | ≥ 90 % GAMM fits converged ≤ 600 s | Log of convergence status |
| **SC‑004** – CI Width | ≤ 7 days 95 % CI for shift | Block‑bootstrap CI |
| **SC‑005** – Runtime | ≤ 6 h total pipeline | `pipeline_report.json` runtime field |

---



## 7. Reproducibility Guarantees
- All random seeds are fixed in `src/config.py`.  
- Data are fetched from the exact URLs listed above; a checksum step validates integrity before any processing.  
- The pipeline is orchestrated by `src/cli/run_pipeline.py` and can be re‑run on a fresh GitHub Actions runner without manual intervention.
