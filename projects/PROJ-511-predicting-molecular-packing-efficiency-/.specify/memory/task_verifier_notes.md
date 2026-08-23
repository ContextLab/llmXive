# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — The repository contains `code/filter_dataset.py`, but the required source data `data/dataset_with_metrics.csv` is absent, and the script has not produced the expected `data/dataset_filtered.csv`. Without the input file the filter cannot be executed, and the output artifact is missing.
- **T018** — The repository lacks the required input file `data/dataset_filtered.csv` and the output file `data/dataset.csv`, so the script cannot be run or verified. Moreover, the provided `code/add_3d_descriptors.py` is truncated and does not show the full logic for loading the CSV, handling missing CIFs, or writing the final dataset with all specified columns. These missing artifacts prevent the task from being considered complete.
