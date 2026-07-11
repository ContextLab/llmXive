# Quickstart: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

## Prerequisites
- Python 3.11+
- `pip`
- Access to HuggingFace Hub (for dataset download)
- Significant temporary disk space requirements are anticipated for data processing and storage during the experimental phase.
- **Expert Access**: A small cohort of domain experts for gold standard annotation (Phase 1).

## Installation

1. **Clone & Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-811-llmxive-follow-up-extending-many-shot-co
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `llama-cpp-python` requires a C++ compiler. On GitHub Actions, this is pre-installed.*
   *Note: `sentence-transformers` is required for SBERT-based CDS baseline.*

## Running the Pipeline

### Step 1: Download & Split Data
```bash
python code/src/download_data.py
# Downloads aaabiao/DAG_sft to data/raw/
# Splits into gold, train, and test sets with varying proportions.
```

### Step 2: Parse CoT Traces (DAG Construction)
```bash
python code/src/parser.py --input data/raw/chains_sample_final_sharegpt.jsonl --output data/processed/dags.json
```
- **Output**: `data/processed/dags.json` containing `max_depth` scores.
- **Validation**: Check `data/processed/parser_log.txt` for cycle errors.

### Step 3: Gold Standard Annotation (Manual)
- **Action**: Recruit a small team of experts to annotate 50 traces from `data/processed/gold_standard_annotations.json`.
- **Output**: `data/processed/gold_standard_annotations.json` filled with ratings.

### Step 4: Validate Metric
```bash
python code/src/validate_metric.py --dags data/processed/dags.json --gold data/processed/gold_standard_annotations.json
```
- **Output**: Correlation coefficient `r`. If `r < 0.6`, halt and report limitation.

### Step 5: Generate Prompts
```bash
python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9
```
- **Output**: `data/processed/prompts/` directory with `strategy_seed.jsonl` files.
- **Note**: Uses SBERT for "Original CDS" strategy.

### Step 6: Run Inference (CPU Only)
```bash
python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b
```
- **Note**: Ensure models are downloaded to `models/` or specified via HF token.
- **Output**: `data/results/inference_log.csv`.

### Step 7: Statistical Analysis (LMM)
```bash
python code/src/analysis.py --input data/results/inference_log.csv
```
- **Output**: `data/results/stats_report.json` (LMM results, p-values).

### Step 8: Update State
```bash
python code/src/update_state.py
```
- **Output**: Updates `state/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co.yaml`.

## Verification
- **Check DAGs**: Ensure `max_depth` variance ≥ 1.5 in `dags.json`.
- **Check Prompts**: Verify examples per prompt.
- **Check Stats**: Confirm LMM interaction p-value and Bonferroni-adjusted results.

## Troubleshooting
- **OOM Error**: Reduce model size to 7B or use `n_batch` smaller in `llama-cpp`.
- **Cycle Detection**: If too many traces are invalid, adjust parser regex rules in `parser.py`.
- **Time Limit**: If > 4 hours, reduce seeds to 5.
