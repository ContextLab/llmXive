# Quickstart: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

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
- Reports how many EDS maps were found via the verified HuggingFace dataset `doe2023/perovskite-eds`. **If none are found**, the pipeline continues with a performance‑only analysis (no abort).

### 2️⃣ Full Pipeline
```bash
python code/main_pipeline.py
```
The orchestrator executes the ordered steps described in `plan.md`.  
Key outputs:

| File | Description |
|------|-------------|
| `data/processed/unified_dataset.csv` | Unified table of performance metrics (and any EDS metadata if available). Includes the `composite_spatial_metric` column (primary composite metric) and nullable spatial‑metric columns. |
| `data/processed/spatial_metrics.csv` | Autocorrelation‑derived lengths, low‑frequency spectral power, and composite metric (may be empty). |
| `data/processed/diffusion_lengths.csv` | Estimated diffusion lengths (may be empty). |
| `results/summary_report.csv` | Correlation coefficients, 95 % CIs, effect‑size q, p‑values, BH‑adjusted p‑values, GAM deviance, Δr, sample counts, and diagnostic flags (conforms to `contracts/results.schema.yaml`). |
| `results/summary_report.pdf` | Human‑readable summary with plots. |
| `results/feasibility_report.json` | Re‑used from step 1 for provenance. |

### 3️⃣ Testing
```bash
# Unit tests for metric extraction (SC‑001)
pytest tests/unit/test_spatial_metrics.py -v

# Unit test for diffusion‑length estimation (FR‑009)
pytest tests/unit/test_diffusion_length.py -v

# Unit test for robustness (SC‑003)
pytest tests/unit/test_robustness.py -v

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
    ├── spatial_metrics.csv   # May be empty
    └── diffusion_lengths.csv # May be empty
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

---


