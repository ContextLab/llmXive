# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was provided that the required directory tree `projects/PROJ-848-llmxive-follow-up-extending-molmomotion/{code,data,specs,state}` actually exists (or contains any files). The implementer’s claim is unsubstantiated, so the task is not verified as completed.
- **T001b** — No evidence of the three `__init__.py` files in `code/src/`, `code/tests/`, or `code/tests/integration/` is provided; without the actual files (or their contents) we cannot confirm they exist or are non‑empty. The required artifacts are missing.
- **T001c** — No evidence of the three required `.gitkeep` files in `data/raw/`, `data/processed/`, or `data/results/` was provided; without these artifacts the task is not satisfied. The implementer must add a non‑empty `.gitkeep` file to each of the three directories.
- **T005a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — No data subsampling script, instruction synthesis module, inference pipeline, or metric analysis code/output was supplied; the claim lacks any tangible artifacts to verify that the dataset was subsampled, instructions generated, predictions run on CPU, or ATE/t‑test results produced. The required files and results are missing.
- **T011** — The `subsample_instances` function is only partially implemented (truncated code, does not read `random_seed`/`target_memory_gb` from `config.py`, and never writes a Parquet file). Moreover, the required output file `data/processed/subsampled_instances.parquet` is missing.
- **T011b** — The repository lacks a `validate_sample_size` function in `code/src/data_loader.py` (the file ends mid‑implementation of `subsample_instances` and never defines the required validation routine). Additionally, the required data file `data/processed/subsampled_instances.parquet` is missing, so the function could not be exercised even if it existed. Both the code artifact and the dataset artifact needed to satisfy T011b are absent.
- **T012** — declared artifact(s) missing/empty/invalid: code/src/instruction_synthesizer.py
