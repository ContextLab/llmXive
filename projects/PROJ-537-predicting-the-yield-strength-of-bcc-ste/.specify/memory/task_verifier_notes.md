# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file system snapshots were provided, so there is no evidence that any of the required folders (`code/`, `data/`, `data/raw/`, `data/intermediate/`, `data/processed/`, `data/provenance/`, `data/results/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`) actually exist. The implementer must supply a view of the project tree or confirmation that these directories have been created and are non‑empty.
- **T003** — No linting or formatting configuration files (e.g., .flake8, pyproject.toml, setup.cfg, or similar) were presented for the `code/` directory, so there is no evidence that flake8 and black have been set up. The required artifacts are missing.
- **T004** — No git‑hook files, configuration, or documentation were provided; the claim contains no artifact showing a pre‑commit hook that checks seeds or imports. The required setup for Git hooks is missing entirely.
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: data/intermediate/merged.csv
- **T020** — The required file `state/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml` does not exist in the repository, so no artifact hashes could have been added. The task cannot be considered completed until this YAML file is present and updated with the appropriate hashes.
- **T031** — declared artifact(s) missing/empty/invalid: data/intermediate/merged.csv
- **T032** — declared artifact(s) missing/empty/invalid: data/results/output.json, schema.yaml
- **T039** — No code, script, function, test, or output file was provided that implements the required logic to compute the standard deviation of key DFT descriptors across the 10 bootstrapped samples from T038 and to produce the `is_stable` boolean. The necessary artifact is missing, so the task is not satisfied.
- **T040** — No SHAP summary or stability distribution plots were provided, nor any files under `data/results/` showing such figures. The required output artifacts are missing, so the task is not satisfied.
- **T041** — declared artifact(s) missing/empty/invalid: data/results/output.json
- **T042** — No updated README.md file was provided; there is no evidence that installation instructions, usage examples, or data source citations were added. The required documentation artifact is missing, so the task is not satisfied.
- **T044** — No code or refactoring artifacts are present; the implementer provided no files, diffs, or documentation showing that any code cleanup or readability improvements were made for the yield‑strength prediction project. Consequently, the required deliverable is missing.
- **T045** — No profiling logs, benchmark results, or any evidence of memory/CPU optimizations are provided, nor any demonstration that the pipeline now runs in under 6 hours on a 2‑core machine. The implementer’s artifacts only discuss data merging and modeling, not the required performance profiling and optimization.
- **T046** — No merged CSV, logs, or test output files are present to demonstrate that the data integration script was executed, that at least 20 valid rows were produced, or that the end‑to‑end pipeline (including model training and evaluation) was run. Without these artifacts the claim cannot be verified.
