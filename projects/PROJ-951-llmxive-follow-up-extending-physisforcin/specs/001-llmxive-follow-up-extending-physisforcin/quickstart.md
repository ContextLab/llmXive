# Quickstart: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (CPU) or Kaggle account (for GPU escape hatch).
- HuggingFace CLI installed (`pip install huggingface_hub`).

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify Environment**:
   ```bash
   python src/utils/verify_env.py
   ```
   *This script checks for PyBullet, CPU availability, and sufficient disk space.*

3. **Configure**:
   Edit `config.yaml` to set:
   - `generation_batch_size`: Number of videos to generate per run.
   - `filter_threshold`: Set to 60.0 (fixed absolute threshold).
   - `training_epochs`: Number of epochs for diffusion training.

## Running the Pipeline

### Step 1: Generate & Filter (User Story 1)
Generates videos and applies the physics filter.
```bash
python src/cli/main.py run-pipeline --stage generate-filter
```
*Output*: `data/curated/curated_dataset.jsonl` and `data/raw/` (raw videos).

### Step 2: Power Analysis (Phase 2)
Estimates variance and determines required sample size.
```bash
python src/cli/main.py run-pipeline --stage power-analysis
```
*Output*: `data/results/power_analysis.json`.

### Step 3: Augmentation (If Needed)
Augments data if n < required.
```bash
python src/cli/main.py run-pipeline --stage augment
```
*Output*: Updated `data/curated/curated_dataset.jsonl`.

### Step 4: Train Model (User Story 2)
Trains the distilled diffusion model on the curated data.
```bash
python src/cli/main.py run-pipeline --stage train
```
*Output*: `models/trained_model.pt` and `data/results/training_log.json`.
*Note*: If CPU fails, the system will automatically attempt to offload to Kaggle (if configured) or raise a specific error.

### Step 5: Evaluate (User Story 3)
Runs benchmarks, downstream tasks, and TOST tests.
```bash
python src/cli/main.py run-pipeline --stage evaluate
```
*Output*: `data/results/benchmark_results.json`.

## Verification

To verify the results:
1. Check `data/results/benchmark_results.json` for `equivalence_flag: true`.
2. Verify the `tost_p_value` is < 0.05.
3. Ensure `data/` checksums match the recorded values in `state/`.

## Troubleshooting

- **PyBullet Crash**: If a video crashes the filter, it is automatically assigned score 0. Check `logs/filter_errors.log`.
- **OOM Error**: If training exceeds 6GB RAM, reduce `config.yaml` `batch_size` to 1.
- **NaN Loss**: The training script will abort and retry with a lower learning rate (max 3 times).