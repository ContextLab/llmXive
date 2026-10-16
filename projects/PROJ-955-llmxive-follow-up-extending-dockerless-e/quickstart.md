# Quickstart: 001-static-dynamic-gap-analysis

This guide walks you through reproducing the analysis on a fresh GitHub Actions runner (or local Linux environment). No GPU is required.

## 1. Clone the Repository & Install Dependencies
```bash
git clone <repo-url>
cd llmxive-project
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Environment (Dry-Run)
To verify that the project structure is correct and the CLI is runnable, execute the dry-run command:
```bash
python -m src.cli.run_pipeline --dry-run
```
This command creates the project directory skeleton and produces a tiny sample result file at `data/results/sample_run.csv`.

## 3. Run the Full Pipeline
Once the environment is verified, run the full analysis pipeline:
```bash
python src/cli/run_pipeline.py \
 --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet \
 --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl \
 --output_dir $(pwd)/output \
 --seed 42
```

## 4. Inspect the Final Report
The final results are aggregated in:
```bash
less output/reports/final_report.md
```

## 5. Run Contract Tests
Validate that all generated artifacts conform to the project schemas:
```bash
pytest -q tests/contract
```

## 6. Run with a Sample (Memory Fallback)
If the dataset exceeds memory limits, use a stratified sample:
```bash
python src/cli/run_pipeline.py \
... \
 --sample_fraction 0.1
```