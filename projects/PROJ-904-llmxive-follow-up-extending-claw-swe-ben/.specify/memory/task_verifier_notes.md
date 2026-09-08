# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or `__init__.py` files were presented; the claim that `data/`, `models/`, `experiments/`, `analysis/`, `tests/`, and `utils/` exist with five `__init__.py` files cannot be verified from the provided artifacts. The required filesystem evidence is missing.
- **T002** — No evidence of any `__init__.py` files being added in the `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/` directory hierarchy is provided; the claim lacks the required artifact listing or file contents. The task cannot be considered done until the missing `__init__.py` files are actually created and shown.
- **T003** — The required file `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/requirements.txt` does not exist, so the project has not been initialized as specified. The existing `code/requirements.txt` is at a different location and does not satisfy the path requirement.
- **T004** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- **T006d** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012a** — No code artifact for `ClawSweBenchLoader` was provided, so we cannot confirm that `datasets.load_dataset(..., streaming=True)` is used or that a `.load()` call on the full dataset has been removed. The required source change is missing.
- **T012c** — The repository does not contain a `write_parquet_and_checksum()` implementation in `code/data/loader.py` (the shown file ends with a truncated `calculate_relevant_lines` function and no such function is present). Additionally, the expected output file `data/filtered_swe_bench_v1.parquet` is missing, so the required artifact was never created. The task therefore remains unfinished.
