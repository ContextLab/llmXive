# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `data/raw/`, `data/processed/`, `data/results/`, `code/`, or `tests/` directories (each containing a `.gitkeep` file) was provided; the claim lacks any artifact showing these folders exist. The implementer must add the directories with non‑empty `.gitkeep` placeholder files.
- **T002** — declared artifact(s) missing/empty/invalid: projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/requirements.txt
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` entries for ruff/black, `.ruff.toml`, or CI scripts invoking these tools) were provided, nor any evidence that the tools have been set up and run. The required artifacts are missing, so the task is not satisfied.
- **T008** — declared artifact(s) missing/empty/invalid: tests/test_data.py, tests/test_metrics.py
- **T014** — The repository contains `code/train.py`, but the shown portion ends before any checkpoint‑saving code and the expected output file `data/results/codebook_v0.pth` is absent. Consequently, the required checkpoint‑saving logic is not present and the artifact the task demanded does not exist.
- **T015** — declared artifact(s) missing/empty/invalid: code/eval_low_res.py
- **T016** — No code, configuration, or log output was presented showing that training loss, reconstruction loss, and codebook usage statistics are now being logged. The required artifact (e.g., updated training script with logging statements or sample log files) is missing, so the task is not satisfied.
