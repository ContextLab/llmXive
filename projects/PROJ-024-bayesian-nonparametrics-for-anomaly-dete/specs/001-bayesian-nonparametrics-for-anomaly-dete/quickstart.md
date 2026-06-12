# Quickstart: Bayesian Nonparametrics for Anomaly Detection in Time Series

This guide walks you through setting up the environment, downloading the benchmark datasets, training the DPGMM, calibrating a threshold, and evaluating performance.

## 1. Clone the Repository & Set Up Environment
```bash
git clone https://github.com/your-org/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.git
cd PROJ-024-bayesian-nonparametrics-for-anomaly-detection
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Config Size (<2 KB)
```bash
stat -c%s code/config.yaml   # should report within a defined limit
```

## 3. Download & Verify Datasets
```bash
python -m code.src.data.download_datasets \
    --output-dir data/raw \
    --datasets electricity traffic synthetic_control
```
The script:
- Uses the deterministic `ucimlrepo` loader.
- Computes SHA256 checksums and writes them to `state/projects/PROJ-024-...yaml`.
- Applies temporal preprocessing (lag features, rolling stats).

## 4. Train the DPGMM Model
```bash
python -m code.src.cli.run_detection train \
    --config code/config.yaml \
    --checkpoint-dir data/processed/results/model_checkpoints
```
- Performs ADVI inference, logs ELBO to `logs/elbo/dpgmm_elbo.log`.
- Saves final checkpoint `dpgmm_checkpoint.pt`.

## 5. Stream Inference & Scoring
```bash
python -m code.src.cli.run_detection infer \
    --checkpoint data/processed/results/model_checkpoints/dpgmm_checkpoint.pt \
    --input data/raw/electricity.csv \
    --output data/processed/results/anomaly_scores.json
```

## 6. Calibrate Threshold
```bash
python -m code.src.cli.run_detection calibrate \
    --scores data/processed/results/anomaly_scores.json \
    --output data/processed/results/threshold.json
```

## 7. Evaluate Performance
```bash
python -m code.src.evaluation.metrics \
    --scores data/processed/results/anomaly_scores.json \
    --threshold data/processed/results/threshold.json \
    --labels data/raw/electricity_labels.csv \
    --output data/processed/results/evaluation_metrics.json
```
The resulting JSON conforms to `evaluation_metrics.schema.yaml`.

## 8. Run Contract Tests
```bash
pytest code/tests/contract/ \
    test_dataset_schema.py \
    test_anomaly_score_schema.py \
    test_evaluation_metrics_schema.py \
    test_threshold_calibrator_schema.py \
    test_anomaly_detector_schema.py \
    test_dpgmm_schema.py \
    test_anomaly_detector_service_schema.py \
    test_threshold_calibrator_service_schema.py \
    --cov=code/src --cov-report term-missing
```
Coverage must be ≥ 80 % (Task T249).

## 9. Verify Cleanup & Integrity (Phase 9.5‑9.6)
```bash
bash scripts/verify.sh
```
The script executes the filesystem verification commands listed in the spec (e.g., `ls -la data/raw/`, `find data/raw/ -type d -name raw`, `stat -c%s code/config.yaml`, etc.) and prints a pass/fail summary.

## 10. Generate Figures & Paper (Optional)
```bash
python -m code.src.analysis.plot_results \
    --metrics data/processed/results/evaluation_metrics.json \
    --output-dir docs/figures
```

All steps are deterministic; re‑running the script from a clean checkout reproduces the exact numbers reported in the final paper.

---