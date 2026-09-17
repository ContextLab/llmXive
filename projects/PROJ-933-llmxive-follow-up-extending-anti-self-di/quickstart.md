# Quickstart Guide: llmXive Anti-Self-Distillation Pipeline

This guide provides the exact commands to set up, run, and validate the **Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information** pipeline (Project PROJ-933).

## Prerequisites

- **Python**: 3.11+
- **Hardware**: CPU-only execution supported (optimized for <6.5GB RAM). GPU optional.
- **Dependencies**: Install via `pip install -r requirements.txt`
- **Environment Variables**:
 - `HF_TOKEN`: Hugging Face access token (required for dataset download)
 - `DATA_CACHE_DIR`: Optional path for caching datasets (default: `data/cache`)

## 1. Setup & Configuration

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
Set the Hugging Face token and dataset paths:
```bash
export HF_TOKEN="your_huggingface_token_here"
export DATA_CACHE_DIR="./data/cache"
```
*Alternatively, copy `config/settings.yaml.example` to `config/settings.yaml` and edit values.*

### Verify Project Structure
Ensure the following directories exist (created by T001):
```
code/
 ├── analysis/
 ├── config/
 ├── data/
 └── models/
data/
results/
```

## 2. Data Acquisition (Phase 0 & US1)

The pipeline ingests **UltraFeedback** and **Dolly** datasets. It filters for prompts with ≥4 distinct reasoning traces and simulates context splits.

### Step 1: Download Datasets
Run the download script to fetch real data with checksumming:
```bash
python code/data/download.py
```
**Output**: `data/raw_datasets/` (cached)

### Step 2: Preprocess & Split Context
Filter prompts and generate the context split file:
```bash
python code/data/preprocess.py
```
**Outputs**:
- `data/context_splits.json`: Prompt IDs, selected privileged context ($c$), and target rationales.
- `data/preprocess_report.json`: Statistics (prompt count, avg tokens, deliberation frequency).

**Validation**: Ensure `data/context_splits.json` contains at least 30 valid prompts (Power Analysis requirement).

## 3. Inference & Teacher Distribution (Phase 3)

Compute the "Teacher Distribution" by averaging logits over all unselected rationales.

### Step 1: Inference-Only Pass
```bash
python code/models/inference_only.py
```
**Outputs**:
- `data/teacher_logits_raw.json`: Raw logits for every unselected rationale.
- `data/teacher_distribution.json`: Averaged logit distribution per prompt.

**Note**: This step is CPU-optimized. Expect ~1-2 hours for the full dataset subset.

## 4. Training Loop (US2)

Execute the Anti-Self-Distillation training loop with gradient inversion.

### Step 1: Run Training
```bash
python code/models/anti_sd_loop.py --config config/settings.yaml
```
**Flags**:
- `--mode anti_sd`: Enable gradient ascent on JS divergence (default).
- `--mode standard`: Run baseline self-distillation for comparison.

**Outputs**:
- `results/training_metrics.json`: Loss curves, JS divergence trajectory, elapsed time.
- `results/memory_log.json`: Peak RAM usage (must be < 6.5GB).
- `results/training_dynamics.json`: Token probabilities and trajectory samples.

**Timeout**: The script enforces a hard 5.5-hour timeout. If exceeded, it saves partial results and exits.

## 5. Analysis & Validation (US3)

Compute diversity metrics, quality scores, and statistical significance.

### Step 1: Compute Metrics
```bash
python code/analysis/visualize.py
```
**Outputs**:
- `results/diversity_metrics.json`: BLEU scores, semantic similarity, deliberation token counts.
- `figures/loss_curves.png`: Visualization of training dynamics.
- `figures/diversity_comparison.png`: Boxplots of diversity metrics.

### Step 2: Statistical Testing
```bash
python code/analysis/statistical_test.py
```
**Outputs**:
- `results/statistical_report.json`: Wilcoxon signed-rank test p-values, effect sizes, and observed power (1-β).

### Step 3: Human Evaluation Proxy
1. Open `docs/rater.html` in a browser.
2. Collect scores from 3 independent raters.
3. Save results to `data/human_scores.csv`.
4. Ingest and analyze:
 ```bash
 python code/analysis/human_score_ingest.py
 ```

## 6. Verification Checklist

Run the following to ensure all artifacts are present and valid:

| Check | Command | Expected Output |
|-------|---------|-----------------|
| Data Split | `test -f data/context_splits.json` | File exists |
| Teacher Dist | `test -f data/teacher_distribution.json` | File exists |
| Training | `test -f results/training_metrics.json` | File exists |
| Stats | `test -f results/statistical_report.json` | File exists |
| Schema | `python code/data/schema_validator.py` | "Validation Passed" |

## Troubleshooting

- **Data Fetch Failed**: Ensure `HF_TOKEN` is set and valid. The script raises `DataFetchError` on failure; no synthetic fallback is performed.
- **OOM (Out of Memory)**: Reduce batch size in `config/settings.yaml` or enable `streaming=True` in `code/data/streaming_loader.py`.
- **Timeout**: If the 5.5h limit is hit, check `results/training_metrics.json` for partial results.

## References

- **Spec**: `specs/001-llmxive-followup/spec.md`
- **Plan**: `plan.md`
- **API Surface**: See `code/` module imports for function signatures.