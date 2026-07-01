# Quickstart: Predicting Species Distribution Shifts

## 1. Prerequisites

* Python 3.11+
* `pip`
* Internet access (for GBIF, eBird, WorldClim, CMIP6 downloads)

## 2. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 3. Data Download

```bash
# Historical occurrence (1970‑2000) and climate
python code/download.py --species-list list_of_species.txt --year-range 1970,2000

# Recent occurrence (2005‑2020) for validation
python code/download.py --species-list list_of_species.txt --year-range 2005,2020 --target recent

# Future climate raster (2050 SSP2‑4.5)
python code/download.py --climate cmip6 --scenario SSP2-4.5 --year 2050
```

## 4. Bias Correction (new)

```bash
python code/bias_correction.py --occurrence data/raw/occurrence_1970_2000.csv \
    --output data/processed/bias_layer.tif
```

Creates `bias_layer.tif` that will be used for weighted background sampling.

## 5. Preprocessing

```bash
python code/preprocess.py --input data/raw/occurrence_1970_2000.csv \
    --bias-layer data/processed/bias_layer.tif \
    --thinning-distance 10
```

* Filters for breeding months, removes duplicates, applies spatial thinning (≥10 km), extracts climate variables, and writes:
  * `data/processed/filtered_thinned.csv`
  * **`logs/preprocess_counts.yaml`**: A YAML log containing `species`, `before_count`, `after_count`, and `timestamp` for every species processed. This file is the Single Source of Truth for data reduction metrics.

## 6. Baseline Model (new)

```bash
python code/baseline.py --data data/processed/filtered_thinned.csv \
    --output metrics/baseline_performance.csv
```

Computes a null model (constant prevalence) for SC‑001 baseline comparison.

## 7. Model Training & Validation

```bash
python code/train.py --data data/processed/filtered_thinned.csv --cv-blocks 5
```

* Trains Random Forest, Bioclim, and **Regularized Logistic Regression (PB)** models.  
* Saves models to `data/artifacts/` and training metrics to `metrics/training_metrics.csv`.

## 8. Future Projection

```bash
python code/project.py --models data/artifacts/ --climate data/raw/cmip6_2050.tif
```

Generates suitability maps for 2050 (`*.tif` per species/algorithm).

## 9. Evaluation & Threshold Handling

```bash
python code/evaluate.py --models data/artifacts/ \
    --test-data data/raw/occurrence_2005_2020.csv \
    --bias-layer data/processed/bias_layer.tif
```

* Computes AUC, TSS, and re‑calibrates thresholds on the test set when ≥100 records are available (fallback to historical threshold otherwise).  
* Writes `metrics/final_results.csv` and logs any `INSUFFICIENT_DATA` flags.

## 10. Sensitivity Analysis (FR‑005, SC‑003)

```bash
python code/sensitivity.py --metrics metrics/final_results.csv \
    --output metrics/sensitivity_report.csv
```

Sweeps Δ ∈ {0.01, 0.05, 0.10} and records headline rates (TPR, FPR, TSS) per model.

## 11. Reporting & Disclaimer (FR‑008)

```bash
# Copy the mandatory associational disclaimer into the report directory
cp reports/associational_disclaimer.txt docs/disclaimer.txt
```

All tables in `metrics/final_results.csv` reference this disclaimer, ensuring that findings are framed as observational.

## 12. Verification

* Check `metrics/final_results.csv` for:
  * Species flagged as `INSUFFICIENT_DATA`.
  * AUC/TSS for each algorithm.
  * Niche‑stability degradation values.
* Review `metrics/sensitivity_report.csv` for threshold sweep results.
* **Verify `logs/preprocess_counts.yaml` exists and contains valid before/after counts for all processed species.**
* Confirm `reports/associational_disclaimer.txt` is present in the final manuscript bundle.

