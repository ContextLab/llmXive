# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
* Python 3.11 or newer  
* Git  
* Access to a GitHub Actions runner **or** a local Linux/macOS environment with ≥ 4 GB RAM  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-505-exploring-the-statistical-relationship-b

# 2️⃣ Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Data Preparation

> **Important** – The required ACE SWICS and NOAA Dst/Kp data are **not** available in any verified open repository. The pipeline therefore **directly generates** a synthetic dataset that matches the required schema.

```bash
# Generate the synthetic aligned hourly dataset
python code/ingestion/generate_synthetic_data.py \
    --seed 42 \
    --output data/processed/aligned.parquet
```

### Verify the dataset
```bash
python code/utils/verify_data.py \
    --input data/processed/aligned.parquet \
    --schema contracts/dataset.schema.yaml
```
The script prints “Schema validation passed” if the file conforms to `dataset.schema.yaml`.

## Run the Full Analysis Pipeline

```bash
python code/main.py
```

`main.py` sequentially executes:

1. Alignment (`align.py`) – (already performed during synthetic generation)  
2. Coupling‑function calculation (`coupling_functions.py`)  
3. Baseline & full regressions (`regression.py`)  
4. ΔR² computation  
5. 5‑fold time‑series cross‑validation (`cross_validation.py`)  
6. Block permutation test (`permutation_test.py`)  
7. Sensitivity & FDR analysis (`sensitivity.py`)  

All results are written to `data/artifacts/`:

| File | Content |
|------|---------|
| `regression_results.csv` | Coefficients, p‑values, VIF, R² for both models |
| `delta_r2.json` | Incremental R² with 95 % CI |
| `cv_metrics.json` | Out‑of‑sample R² (baseline & full) |
| `permutation_results.json` | Null distributions, p‑values, significance flags |
| `sensitivity.json` | Effect of α = 0.01/0.05/0.10 on number of significant predictors |
| `plots/` | Visualizations (coefficient bar plots, null‑distribution histograms, CV R² boxplots) |

**Interpretation**: Because the dataset is synthetic, the output demonstrates that the statistical workflow functions correctly. No scientific claim about the real solar‑wind–geomagnetic relationship should be drawn from these numbers.

## Testing

```bash
pytest tests/
```

The test suite checks:

* I/O helpers (`code/utils/io.py`) work with and without `pyarrow`.  
* Schema compliance of generated parquet files.  
* Correctness of coupling‑function formulas.  
* End‑to‑end pipeline produces all expected artifact files.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `ImportError: pyarrow` when saving parquet | `pyarrow` not installed on the runner | The I/O helper automatically falls back to Pandas’ `fastparquet` engine; ensure `fastparquet` is installed (`pip install fastparquet`). |
| MemoryError during regression | Attempting to load an unexpectedly large real dataset | Use the synthetic fallback (default) or process real data in chunks (not needed for synthetic). |
| “Schema validation failed” | Generated file missing a required column | Re‑run `generate_synthetic_data.py` – it always produces the full schema. |

---



