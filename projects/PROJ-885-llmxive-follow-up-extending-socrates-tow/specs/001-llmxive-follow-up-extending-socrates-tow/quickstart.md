# Quickstart: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

## 1. Prerequisites
- Python 3.11 or newer  
- ≥ 7 GB RAM, ≥ 2 vCPU (GitHub Actions free tier)  
- Internet access for dataset download  

## 2. Installation
```bash
# Clone the repository (already done in CI)
cd projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## 3. Data Download & Generation
```bash
# Download SoCRATES prompts (streaming) and generate oversampled trajectories
python src/data/generate_trajectories.py --download-only   # creates data/raw/
python src/data/generate_trajectories.py --oversample-high-difficulty --num-trajectories 120
```
*Outputs:*  
- `data/raw/socrates_prompts.parquet` (checksum verified)  
- `data/processed/filtered_trajectories.jsonl` (experiment set, ≥ 40 % high‑difficulty)  
- `data/processed/generation_stats.json` (total count, oversampling ratio)  
- `data/results/oversampling_report.json` (must show ≥ 40 % high‑difficulty)  

## 4. Train the State Classifier
```bash
# Split the dataset into training and experiment subsets
python src/data/split_dataset.py --train-ratio 0.6

# Train the logistic‑regression classifier on the training split
python src/data/classifier_training.py
```
*Outputs:* `models/state_classifier.pkl` and `data/results/feature_independence_audit.json`.

## 5. Run the Full Experiment (CPU‑Only)
```bash
python src/experiments/runner.py \
  --models llama-3-8b,mistral-7b,gemma-2b,phi-2b,openchat-3.5,starling-7b,qwen-7b,gemma-7b \
  --conditions adapter,static \
  --batch-size 4
```
*Outputs:* `data/results/experiment_logs/<model_name>/<condition>.jsonl` and `data/results/scope_adjustments.json`.

## 6. Statistical Analysis
```bash
python src/analysis/stats_utils.py
```
*Outputs:* `data/results/statistical_report.json`, `data/results/threshold_sensitivity_report.json`.

## 7. Validation & Verification
```bash
# End‑to‑end integration test
python tests/integration/test_full_pipeline.py
```
*Expected:* The test completes without error, confirming the pipeline runs end‑to‑end.

## 8. Troubleshooting
- **Out‑of‑Memory**: Reduce `--batch-size` or drop the largest model from `--models`.  
- **CUDA Error**: Ensure `device="cpu"` is enforced; the runner will abort if any CUDA import is detected.  
- **Oversampling Failure**: Check `data/results/oversampling_report.json`; regenerate with a different random seed (`--seed <int>`).  
- **Low Confidence Excess**: Review `data/results/threshold_sensitivity_report.json` to see how many neutral‑monitoring runs were produced.

---

