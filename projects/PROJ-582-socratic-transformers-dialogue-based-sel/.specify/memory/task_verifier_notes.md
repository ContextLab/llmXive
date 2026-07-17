# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: src/__init__.py, tests/__init__.py, requirements.txt
- **T003** — No configuration files (e.g., `pyproject.toml`, `ruff.toml`, or Black settings) or scripts enabling ruff/black linting/formatting are present in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. Without these artifacts, the task of configuring the tools cannot be confirmed as completed.
- **T004** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/results/`) or the `.gitkeep` placeholder files is provided; the implementer’s claim is unsubstantiated. The next implementer must create the three data sub‑directories and add a `.gitkeep` file in each to satisfy the task.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils/model_loader.py
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/metrics.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/static_extractor.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/generate_dialogue.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/ablation.py
- **T029** — No code, data, or results showing a sensitivity‑analysis sweep over the specified error‑threshold values (0.01, 0.05, 0.1) are present. The implementer supplied no artifact (e.g., script, log, or figure) that demonstrates the sweep or its robustness validation, so the requirement is unmet.
- **T032** — No research.md file or its contents were provided, so we cannot confirm that it was updated to distinguish the two concepts and address Ada Lovelace’s concerns. The required artifact is missing.
- **T033** — No updated `spec.md` or excerpt showing the problem statement rewritten to use “evolutionary pressure” / “negative selection on belief” and to address David Krakauer’s review is provided; without that artifact we cannot confirm the requirement was met. The implementer must supply the revised specification file (or its relevant section) demonstrating the changes.
- **T034** — No linting or formatting reports, diff logs, or updated source files are provided to demonstrate that `ruff check` and `black --check` were run and that all violations were fixed. The required evidence of zero linting/formatting errors is missing.
