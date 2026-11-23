# Quickstart Guide

This guide describes how to run the full analysis pipeline for the llmXive follow-up study.

## Prerequisites

- Python 3.11+
- pip
- A HuggingFace account with access to the `aaabiao/DAG_sft` dataset (if not public).

## Setup

1. **Clone the repository** (if not already done).
2. **Install dependencies**:
 ```bash
 cd projects/PROJ-811-llmxive-follow-up-extending-many-shot-co
 python -m venv code/.venv
 source code/.venv/bin/activate
 pip install -r requirements.txt
 ```
3. **Configure environment** (optional):
 Create a `.env` file in the project root with:
 ```
 DATASET_NAME=aaabiao/DAG_sft
 SEEDS=0 1 2 3 4 5 6 7 8 9
 ```

## Execution Order

The pipeline consists of several stages. Run them in order.

### 1. Data Preparation & Manifest Generation (T018)

Generate the DAG manifest containing dependency depths for all valid traces.

```bash
python code/scripts/generate_dag_manifest.py
```

**Output**: `data/processed/dag_manifest.json`

### 2. Gold Standard Template Generation (T015b)

Generate a template for gold standard annotations if not present.

```bash
python code/scripts/generate_gold_standard_template.py
```

**Output**: `data/processed/gold_standard_annotations.json` (if missing)

### 3. Prompt Generation (T022, T023, T024c, T026)

Generate prompts using different strategies (Logical Ascending, Logical Random, Original CDS).

```bash
python code/scripts/run_batch_strategies.py
```

**Output**: `data/processed/prompts/` directory with strategy-specific files.

### 4. Inference (T032)

Run inference on the generated prompts.

```bash
python code/src/inference.py --model-class reasoning --seed 0
# Repeat for other seeds and model classes
```

**Output**: `data/results/inference_log.csv`

### 5. Statistical Analysis (T035a, T035b, T038)

Perform LMM analysis and generate the statistical report.

```bash
python code/src/analysis.py
```

**Output**: `artifacts/stats_report.md`

## Verification

After running the pipeline, verify the outputs:

1. Check `data/processed/dag_manifest.json` for valid entries.
2. Check `artifacts/stats_report.md` for the LMM results and p-values.
3. Ensure no synthetic data was used (check logs for "Failed to load dataset" errors if real data is unreachable).

## Troubleshooting

- **Dataset Loading Errors**: Ensure you have internet access and the dataset name is correct.
- **Memory Errors**: The pipeline uses streaming for data loading. If you encounter memory issues, check your chunking logic.
- **Missing Artifacts**: Ensure all scripts in the execution order were run successfully.

## Notes

- The `quickstart.md` command for `prompt_gen.py` and `inference.py` has been reconciled to use the correct arguments (`--manifest` and `--model-class` respectively).
- The `download_data.py` and `validate_metric.py` scripts mentioned in the original run-book are not required for the current implementation flow, as data loading is handled by `generate_dag_manifest.py` and metric validation is integrated into the analysis scripts.
