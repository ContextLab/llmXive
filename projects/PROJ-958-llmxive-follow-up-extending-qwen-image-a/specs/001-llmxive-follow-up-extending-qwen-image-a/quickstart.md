# Quickstart: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

## Prerequisites
- Python 3.11+
- Git
- Hugging Face CLI (`pip install huggingface_hub`)
- Access to GitHub Actions (for CI) or local environment with sufficient RAM for the build environment

## Installation
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   cd code
   pip install -r requirements.txt
   ```
3. Set up environment variables (optional):
   ```bash
   export HF_TOKEN=your_token  # If needed for gated datasets (none expected here)
   ```

## Running the Pipeline
The pipeline is executed in sequential steps. Each step can be run independently for debugging.

### Step 1: Fetch & Validate Data
```bash
python 01_fetch_data.py
python 02_validate_data.py
```
- Downloads IA-Bench and WISE-Verified datasets to `data/raw/`.
- Runs Reference-Validator on all datasets (T006b-2).
- **Validates Reference Independence**: Checks that `reference_description` is distinct from `prompt`.
- Computes checksums and logs to `data/raw/checksums.txt`.

### Step 2: Compute Complexity Scores
```bash
python 03_compute_complexity.py
```
- Outputs `data/derived/complexity_scores.csv`.
- Logs warnings for unparseable prompts.

### Step 3: Route Prompts & Sample Counterfactuals
```bash
python 04_route_prompts.py
```
- Outputs `data/derived/routed_prompts.csv`.
- **Randomly selects a subset** of Low/Medium prompts for Baseline execution (flagged as `is_counterfactual_sample=True`).
- Logs routing decisions and sampling flags.

### Step 4: Generate Images
```bash
python 05_generate_images.py
```
- Executes Qwen-Image-Agent for **High** and **Counterfactual Sample** prompts.
- Uses rule-based expansion for **Low/Medium Non-Sampled** prompts.
- Saves images to `data/derived/generated_images/`.
- Logs latency and tokens to `generation_log.jsonl`.

### Step 5: Compute Fidelity
```bash
python 06_compute_fidelity.py
```
- Uses CLIP ViT-B/32 to score image-reference pairs.
- Calculates Delta only where Baseline exists.
- Outputs `data/derived/fidelity_scores.csv`.

### Step 6: Classify Domains
```bash
python 07_classify_domains.py
```
- Uses ResNet-50 to classify images.
- Outputs `data/derived/domain_labels.csv`.

### Step 7: Regression & Threshold Detection
```bash
python 08_regression_analysis.py
```
- Performs piecewise regression on **High + Counterfactual Sample** data.
- Includes LRT and Permutation Test.
- Outputs `data/results/knee_point_analysis.json`.

### Step 8: Stratified Analysis
```bash
python 08_regression_analysis.py --stratify
```
- (Integrated into Step 7) Outputs `data/results/stratified_results.json`.

### Step 9: Efficiency Report
```bash
python 11_efficiency_report.py
```
- Outputs `data/results/efficiency_metrics.csv`.

## Testing
Run unit and integration tests:
```bash
pytest tests/unit
pytest tests/integration
```

Run contract tests:
```bash
pytest tests/contract
```

## Reproducibility
- All random seeds are set in `code/utils/config.py`.
- Datasets are fetched from canonical sources; checksums stored in `data/raw/checksums.txt`.
- To reproduce: run `./reproduce.sh` (provided) which executes all steps in order.

## Troubleshooting
- **CLIP OOM**: Reduce batch size in `06_compute_fidelity.py`.
- **Qwen GPU Error**: Offload to Kaggle; ensure `device="cuda"` is set.
- **Dataset Fetch Fail**: Check Hugging Face connectivity; use `streaming=True`.
- **Reference Independence Fail**: If many prompts fail independence check, review WISE-Verified dataset structure; may need manual curation.