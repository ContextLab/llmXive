# Quickstart: Running the Circadian‑MetS Analysis Pipeline

> The following steps assume you are on a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the Repository & Set Up Environment
```bash
git clone https://github.com/yourorg/circadian-metabolic-correlation.git
cd circadian-metabolic-correlation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Data Checksums (Optional but recommended)
```bash
python scripts/verify_checksums.py   # reads data/checksums.txt and aborts on mismatch
```

## 3. Download Raw Datasets
```bash
python scripts/download_data.py \
    --gtex-url https://huggingface.co/datasets/CNX-PathLLM/GTEx-WSI-Description/resolve/main/data/test-00000-of-00001.parquet \
    --mesa-url https://huggingface.co/datasets/MESA2025/mesa/resolve/main/device_1/music/rD9E2aF8K4.json \
    --out-dir data/raw
```
*The script streams the GTEx parquet to avoid memory spikes and writes a local copy.*

## 4. Pre‑process Phenotypes & Classify MetS
```bash
python scripts/prepare_phenotypes.py \
    --mesa data/raw/mesa.json \
    --out data/processed/donors.parquet
```
*Outputs `donors.parquet` with MetS labels, severity score, and sensitivity‑analysis log (FR‑001, FR‑002, SC‑005).*

## 5. Extract Core Gene Expression
```bash
python scripts/extract_expression.py \
    --donors data/processed/donors.parquet \
    --genes PER1 BMAL1 CLOCK NR1D1 RORA \
    --out data/processed/expression.parquet
```

## 6. Differential Expression (Hierarchical ANCOVA) & Global FDR
```bash
python scripts/differential_expression.py \
    --donors data/processed/donors.parquet \
    --expr data/processed/expression.parquet \
    --out data/processed/de_results.csv
```

## 7. Gene‑Trait Correlations
```bash
python scripts/gene_trait_correlation.py \
    --donors data/processed/donors.parquet \
    --expr data/processed/expression.parquet \
    --out data/processed/correlation_results.csv
```

## 8. Logistic Regression (Primary) & Auxiliary Traits‑Only Model
```bash
python scripts/logistic_model.py \
    --donors data/processed/donors.parquet \
    --expr data/processed/expression.parquet \
    --out-dir data/processed/logistic/
```
*Creates `logistic_model_coefficients.csv`, `auxiliary_traits_coefficients.csv`, `cv_performance.csv`, and batch‑sensitivity diagnostics.*

## 9. Power Analysis (FR‑011)
```bash
python scripts/power_analysis.py \
    --donors data/processed/donors.parquet \
    --out data/processed/power_report.txt
```

## 10. External Validation (MESA Blood)
```bash
python scripts/validate_mesa.py \
    --mesa-data data/raw/mesa.json \
    --model data/processed/logistic/logistic_model.pkl \
    --out data/processed/validation_results.csv
```

## 11. Generate Figures & Summary Report
```bash
python scripts/report.py \
    --de data/processed/de_results.csv \
    --corr data/processed/correlation_results.csv \
    --logreg data/processed/logistic/logistic_model_coefficients.csv \
    --aux data/processed/logistic/auxiliary_traits_coefficients.csv \
    --cv data/processed/logistic/cv_performance.csv \
    --validation data/processed/validation_results.csv \
    --out-dir figures/
```

## 12. Run All Tests
```bash
pytest -v
```
*Contract tests validate schema compliance (`contracts/*.schema.yaml`).*

## 13. CI Execution (CPU‑Only Enforcement)
The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml`. This workflow:
1. Installs dependencies from `requirements.txt`.
2. Executes `python -c "import torch; assert not torch.cuda.is_available()"` to guarantee CPU‑only execution.
3. Runs the full pipeline in the order shown above.
4. Executes `pytest` with contract validation.

## 14. Clean Up (optional)
```bash
rm -rf data/raw
```

All scripts are located under `scripts/`. Random seeds are fixed (`seed=42`) to ensure reproducibility (Constitution I). For detailed parameter options, see each script’s `--help` output.

---

