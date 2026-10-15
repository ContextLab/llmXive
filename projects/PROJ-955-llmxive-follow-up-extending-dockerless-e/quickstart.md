# Quickstart: 001-static-dynamic-gap-analysis

This guide demonstrates the minimal end‑to‑end execution of the
pipeline on a fresh environment.

## Run the full ingestion pipeline
```bash
python -m src.cli.run_pipeline \
 --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet \
 --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl \
 --output_dir output \
 --seed 42
```

The command will:

1. Create the required project directories (`data/`, `interim/`, `features/`,
 `models/`, `reports/`).
2. Download the raw SWE‑Gym and Multi‑SWE‑RL datasets.
3. Verify their SHA‑256 checksums (if listed in `plan.md`).
4. Produce `data/patches.csv` (unified patch table).
5. Write execution logs under `data/execution_logs/`.
6. Print a short summary of the ingestion step.

After the command finishes without error, you should see log messages
indicating successful download, checksum verification, and the number of
patches ingested.

You can inspect the generated CSV with:
```bash
head data/patches.csv
```

The tiny dry‑run example is still available:
```bash
python -m src.cli.run_pipeline --dry-run
```