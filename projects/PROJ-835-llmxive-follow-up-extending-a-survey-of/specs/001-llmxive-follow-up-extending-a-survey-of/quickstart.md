# Quickstart: LLMXive Follow-up: Latent Anomaly Detection

## Prerequisites
- Python 3.11+
- Git
- Access to a GitHub Actions free-tier runner (or local machine with sufficient RAM and CPU cores to support the method).

## 1. Clone and Setup
```bash
git clone <repo-url>
cd projects/PROJ-835-llmxive-follow-up-extending-a-survey-of
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Data Preparation
The pipeline automatically downloads and verifies datasets from the verified sources.
```bash
# Run the data download and verification step
python src/data/download.py
```
*Note: This will fetch the LALM Adversarial/Benign datasets from the verified HuggingFace URLs and compute checksums. It will also validate label independence.*

## 3. Run the Full Pipeline
Execute the end-to-end pipeline (Extraction -> Training -> Evaluation -> State Update):
```bash
python src/cli/run_pipeline.py
```
**Expected Output**:
- `data/processed/embeddings.parquet`
- `models/logistic_regression.pkl`
- `results/report.md`
- `results/resource_log.json`
- `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` (Updated with artifact hashes)

## 4. Verify Results
Check the generated report for:
- **Recall**: Should be reported with confidence intervals.
- **F1 vs Baseline**: Confirm improvement over stratified random baseline.
- **Random Noise Baseline**: Verify that jailbreaks are outliers relative to random noise, not just the benign cluster.
- **Resource Usage**: Ensure RAM < 7 GB and Time < 6 hours.

## 5. Reproducibility Check
To ensure reproducibility, re-run the pipeline with the same random seed:
```bash
python src/cli/run_pipeline.py --seed 42
```
Verify that the checksums of the output artifacts in the `state` file match the previous run.