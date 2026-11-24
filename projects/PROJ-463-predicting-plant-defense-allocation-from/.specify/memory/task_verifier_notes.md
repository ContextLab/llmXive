# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows `src/__init__.py`, `tests/__init__.py`, and the three `.gitkeep` files under `data/raw`, `data/processed`, and `data/traits`, but there is no confirmed presence of `data/manifests/.gitkeep`, `data/synthetic/.gitkeep`, nor the required flag file `data/.dir_setup_complete`. These missing files prevent the task from being fully satisfied.
- **T003a-fix** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=1
- **T003b-install-deps** — No artifact (e.g., a shell script, log file, or captured command output) showing that the specified `conda install …` command was run, nor any evidence that the subsequent version checks (`fastp --version`, etc.) were executed and returned exit code 0. Without such execution evidence, the task’s installation and verification requirements are not satisfied.
- **T003c-fix** — declared artifact(s) missing/empty/invalid: data/manifests/env_validation.json
- **T007-fix** — declared artifact(s) missing/empty/invalid: src/utils/setup_dirs.py
- **T008** — The `tests/unit/test_download.py` file exists, but it imports a non‑existent function `validate_fastq_download` (no such function is defined in either `src/data/download.py` or `code/src/data/download.py`) and uses a `ManifestEntry` schema that does not match the actual `ManifestEntry` model in `src/utils/schemas.py`. Consequently the unit test cannot run or validate FASTQ downloads as required. The missing/incorrect implementation must be added and the test adjusted to the real schema.
- **T009** — The `tests/unit/test_batch_correction.py` file exists and contains many relevant test cases, but it is not a runnable unit test because it references `os.path.exists` without importing the `os` module, causing a `NameError` during execution. This missing import prevents the test suite from actually verifying the batch‑correction metric calculations. Adding the missing `import os` (and ensuring the test runs without errors) is required to satisfy the task.
- **T010** — The `tests/integration/test_preprocess.py` file is present, but it never generates synthetic FASTQ files nor invokes the full `run_preprocessing_pipeline` function; it manually creates a counts matrix and computes TPM, so the test does not actually exercise the complete preprocessing pipeline as required. The integration test therefore fails to satisfy the “full preprocessing pipeline” requirement (step 1) and is incomplete.
- **T037** — declared artifact(s) missing/empty/invalid: src/analysis/pathway_aggregation.py, data/processed/pathway_mappings.json, data/processed/pathway_features.csv
- **T024** — declared artifact(s) missing/empty/invalid: tests/unit/test_validation.py
- **T053** — declared artifact(s) missing/empty/invalid: src/analysis/tissue_specificity.py
- **T030** — declared artifact(s) missing/empty/invalid: src/cli/run_pipeline.py
- **T050** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity_analysis.py
- **T051** — declared artifact(s) missing/empty/invalid: src/cli/report_generator.py
