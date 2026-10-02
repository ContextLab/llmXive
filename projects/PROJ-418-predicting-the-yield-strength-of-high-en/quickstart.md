# Quickstart for Predicting HEA Yield Strength

This document provides a minimal, reproducible set of commands to
execute the full analysis pipeline from raw data acquisition to final
reporting.

## Prerequisites

- Python 3.9+ (virtual environment recommended)
- All dependencies installed via `pip install -r requirements.txt`

## Steps

1. **Create the required directory structure** (already performed by `T001a`).

2. **Install the project dependencies**

 ```bash
 pip install -r requirements.txt
 ```

3. **Run the full pipeline with checksum verification**

 The original command attempted to invoke a non‑existent `src.pipeline.run`
 module. The corrected entry point is the script
 `code/run_pipeline_with_checksum.py`, which also performs the
 FR‑009 checksum validation before proceeding.

 ```bash
 python code/run_pipeline_with_checksum.py --seed 42 --output-dir output/
 ```

 This command will:

 - Download the raw HEA dataset (`data/raw/heas_raw.csv`) if it is not
 already present.
 - Verify that the SHA‑256 checksum recorded in the state file matches
 the actual file hash; on mismatch it aborts with a clear error.
 - Execute the data preprocessing, descriptor calculation, and all
 downstream model training/evaluation steps, producing the expected
 artifacts such as `data/processed/hea_descriptors.csv`,
 `output/metrics.json`, `output/report.md`, etc.

4. **Validate the quick‑start execution**

 After the pipeline finishes, you can run the built‑in validation script
 to ensure all expected artifacts exist and conform to their schemas:

 ```bash
 python code/validate_quickstart.py
 ```

## Expected outputs

- `data/raw/heas_raw.csv` – raw experimental dataset.
- `data/processed/hea_descriptors.csv` – descriptor table.
- `output/metrics.json` – model performance metrics.
- `output/report.md` – comprehensive analysis report.
- Additional JSON files (e.g., `output/permutation_results.json`,
 `output/stability_rankings.json`) as described in the project
 specifications.

If any step fails, consult the log messages printed to the console;
they will indicate whether a checksum mismatch (FR‑009) or another
issue caused the abort.