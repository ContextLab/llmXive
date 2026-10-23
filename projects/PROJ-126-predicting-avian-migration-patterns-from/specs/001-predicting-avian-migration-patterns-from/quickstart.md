# Quickstart: Predicting Avian Migration Patterns

## Prerequisites
- **Python** ≥ 3.11
- **Git** (any recent version)
- **Disk space**: ≥ 10 GB (raw downloads)
- **RAM**: ≥ 7 GB (pipeline uses streaming; 8 GB recommended)
- **NASA Earthdata token**: *Not required* – MODIS data are obtained from the verified HuggingFace NPZ (see Dataset Strategy).

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-126-predicting-avian-migration-patterns-from

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Data Setup (automated)

```bash
# Run the data loader – downloads both EBD and MODIS assets
python code/data_loader.py
```

The script will:
- Stream the eBird CSV from HuggingFace to `data/raw/ebd_subset.csv`.
- Download the verified MODIS 8‑day LST and 16‑day NDVI NPZ archive from HuggingFace, aggregate to weekly means, and store them under `data/raw/`.
- Verify MD5 checksums and record them in `state/...yaml`.

## Run the Full Pipeline

```bash
bash code/run_pipeline.sh
```

The script executes the stages in order:

1. **Preprocessing** – creates `data/processed/first_arrival_sweep.csv` (validated against **both** `dataset.schema.yaml` **and** `dataset_schema.schema.yaml`).  
2. **Model training** – fits three XGBoost models (Temp‑only, NDVI‑only, Combined) with the effort covariate and low‑rank spatial spline features; saves models under `data/outputs/models/`.  
3. **Evaluation** – writes `data/processed/metrics.json` (includes `spatial_bootstrap_p` and secondary `dm_p_value_hac`).  
4. **Visualization** – produces `migration_map.png` and `shap_summary.png` in `data/outputs/`.  
5. **Provenance** – logs file‑level provenance to `data/outputs/provenance.log`.  

## Verification Checklist

1. **Metrics sanity**  

   ```bash
   cat data/processed/metrics.json
   ```

   - `combined_model_rmse` must be lower **than** `naive_baseline_rmse`.  
   - Primary `spatial_bootstrap_p` < 0.05 (Bonferroni‑adjusted) and secondary `dm_p_value_hac` < 0.05 confirm significance.  

2. **Run unit tests**  

   ```bash
   pytest tests/ -v
   ```

   All tests should pass, including the runtime‑monitor test that checks `peak_rss_gb ≤ 7` and `elapsed_time_hours ≤ 6`.  

3. **Output inspection**  

   ```bash
   ls -lh data/outputs/
   ```

   - PNG maps (`migration_map.png`, `shap_summary.png`) should each be ≥ 500 KB.  
   - `provenance.log` should contain lines linking each output file to its source(s).  

If any of the above checks fail, the CI will flag the run and the implementation will be re‑run after fixing the issue.

---

