# Data Model: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Entity Definitions

### 1. ElementalMap (optional)
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique sample identifier (matches `DevicePerformance.id`). |
| `element` | `string` (enum: `"Pb"`, `"I"`, `"MA"`) | Element represented. |
| `raw_path` | `string` | Path to original EDS file under `data/raw/`. |
| `processed_path` | `string` | Path to aligned/masked array under `data/processed/`. |
| `pixel_size_nm` | `number` | Spatial resolution (nm per pixel). |
| `dimensions` | `array[integer, 2]` | Width × Height in pixels. |
| `mask_percentage` | `number` (0‑1) | Fraction of pixels masked due to defects. |
| `co_location_method` | `string` | Method used for co‑location validation (e.g., `"ID+scan_index"`). |
| `link_verified` | `boolean` | `true` if a programmatic link to an EDS file was found. |

### 2. DevicePerformance
| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Must match `ElementalMap.id` when maps exist. |
| `pce` | `number` | Power‑Conversion Efficiency (%). |
| `j_sc` | `number` | Short‑circuit current density (mA cm⁻²). |
| `v_oc` | `number` | Open‑circuit voltage (V). |
| `source_url` | `string` | URL of the JSON/CSV source. |

### 3. SpatialMetric (optional, present only if EDS maps are available)
| Field | Type | Description |
|-------|------|-------------|
| `map_id` | `string` | FK → `ElementalMap.id`. |
| `element` | `string` (enum: `"Pb"`, `"I"`, `"MA"`) | |
| `correlation_length_exp` | `number` (nullable) | 1/e decay from exponential fit (nm). |
| `correlation_length_gauss` | `number` (nullable) | 1/e decay from Gaussian fit (nm). |
| `correlation_length_power` | `number` (nullable) | 1/e decay from power‑law fit (nm). |
| `best_fit_model` | `string` (enum: `"exponential"`, `"gaussian"`, `"power-law"`) (nullable) | Model selected by AIC. |
| `aic_score` | `number` (nullable) | AIC of the best model. |
| `low_freq_spectral_power` | `number` | Integrated power in 0‑0.1 cycles/pixel. |
| `is_undefined` | `boolean` | Autocorrelation never decayed to 1/e within image bounds. |
| `is_censored` | `boolean` | True if correlation length exceeds image dimension. |
| `censored_value` | `number` (nullable) | Image dimension used as lower bound when censored. |

### 4. AnalysisResult
| Field | Type | Description |
|-------|------|-------------|
| `pair` | `string` (enum: `"PCE_Jsc"`, `"PCE_Voc"`, `"Jsc_Voc"` ) | Performance variable pair analyzed. |
| `metric_type` | `string` (enum: `"pearson"`, `"spearman"`, `"gam"` ) | Statistical method used. |
| `r_value` | `number` | Correlation coefficient (Pearson r or Spearman ρ). |
| `p_value` | `number` | Raw p‑value. |
| `p_value_adj` | `number` | Benjamini‑Hochberg adjusted p‑value (when multiple tests). |
| `gam_deviance_explained` | `number` (nullable) | Fraction of deviance explained by GAM (if GAM applied). |
| `robustness_delta_r_max` | `number` (nullable) | Max Δr from LOO‑CV. |
| `n_samples` | `integer` (≥ 1) | Number of samples used. |
| `sensitivity_excluded` | `boolean` | `true` if sample excluded by FR‑008 sensitivity analysis. |
| `co_location_status` | `string` (enum: `"verified"`, `"mismatch"`, `"ambiguous"` ) | Outcome of co‑location validation. |
| `depth_validation_status` | `string` (enum: `"valid"`, `"flagged"`, `"excluded"` ) | Result of depth‑resolution check. |

## Data Flow Overview
1. **Feasibility** → `feasibility_report.json` (counts of requested vs. found EDS maps).  
2. **Ingestion** → `unified_dataset.csv` (populated `DevicePerformance` and optional `ElementalMap`).  
3. **Validation** → `co_location_status.csv`, `depth_status.csv`.  
4. **Metric Extraction** → `spatial_metrics.csv` (may be empty).  
5. **Modeling** → `summary_report.csv`.  
6. **Report** → `summary_report.pdf`.

## Integrity Constraints
- `DevicePerformance.id` **must be unique**.  
- If an `ElementalMap` exists, its `id` **must match** a `DevicePerformance.id`.  
- `pce` **> 0** and **< 50**.  
- `mask_percentage` **∈ [0, 1]**.  
- When `is_undefined` = `true`, all `correlation_length_*` fields are `null`.  
- Samples with `co_location_status` ≠ `"verified"` are excluded from any statistical modeling.  

---



## Quickstart: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Prerequisites
- Python 3.11 or newer  
- Git  
- Access to GitHub Actions (or a local Linux environment with ≥ 7 GB RAM)  

## Installation
```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-204-quantifying-the-impact-of-spatial-correl

# 2️⃣ Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Run

### 1️⃣ Feasibility Check (always runs first)
```bash
python code/data/download_feasibility.py
```
- Produces `results/feasibility_report.json`.  
- Reports how many EDS maps were found. **If none are found**, the pipeline continues with a performance‑only analysis (no abort).

### 2️⃣ Full Pipeline
```bash
python code/main_pipeline.py
```
The orchestrator executes the ordered steps described in `plan.md`.  
Key outputs:

| File | Description |
|------|-------------|
| `data/processed/unified_dataset.csv` | Unified table of performance metrics (and any EDS metadata if available). |
| `data/processed/spatial_metrics.csv` | Autocorrelation‑derived lengths and spectral power (may be empty). |
| `results/summary_report.csv` | Correlation coefficients, p‑values, BH‑adjusted p‑values, GAM deviance, Δr, and sample counts (conforms to `contracts/results.schema.yaml`). |
| `results/summary_report.pdf` | Human‑readable summary with plots. |
| `results/feasibility_report.json` | Re‑used from step 1 for provenance. |

### 3️⃣ Testing
```bash
# Unit tests for metric extraction (SC‑001)
pytest tests/unit/test_spatial_metrics.py -v

# Integration test for the whole pipeline (including feasibility logic)
pytest tests/integration/test_pipeline.py -v
```

## Expected Directory Layout After a Successful Run
```text
data/
├── raw/                     # Original JSON/CSV performance data; any EDS maps if found
└── processed/
    ├── unified_dataset.csv
    ├── co_location_status.csv
    ├── depth_status.csv
    └── spatial_metrics.csv   # May be empty
results/
├── feasibility_report.json
├── summary_report.csv
└── summary_report.pdf
logs/
└── pipeline.log            # Detailed log of each step
```

## Re‑Running or Updating
- To **re‑run** with a fresh seed: `python code/utils/seed.py set 42` before `main_pipeline.py`.  
- To **add new samples** (e.g., after a database update), simply re‑execute `main_pipeline.py`; the feasibility script will automatically detect newly available EDS maps.
