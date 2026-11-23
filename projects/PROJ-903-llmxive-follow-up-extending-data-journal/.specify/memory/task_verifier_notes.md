# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001i** — The evidence shows the `raw/` directory exists under the project path, but the required `output/` directory is missing, and the `processed/` directory is located at `data/processed/` instead of under `projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/processed/`. Both missing and mis‑placed directories must be created in the correct locations.
- **T002a** — The `requirements.txt` file is present, but it does not contain **pinned** versions (exact `==` specifications) for the required libraries; it uses open-ended `>=` constraints and also includes many unrelated packages. This fails the task’s requirement to provide a requirements file with pinned versions for the listed dependencies.
- **T002b** — The only artifact provided is the `requirements.txt` file; there is no virtual environment directory, activation script, or any evidence (e.g., `pip list`/`pip freeze` output) that the dependencies were installed. The task explicitly required creating a `venv` and installing the listed packages, which is missing.
- **T002c** — No linting/formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or pre‑commit hook scripts) or evidence of ruff/black being set up were provided; without these artifacts the requirement to configure ruff and black cannot be verified.
- **T054** — declared artifact(s) missing/empty/invalid: tests/integration/test_streaming.py
- **T045** — declared artifact(s) missing/empty/invalid: code/narrative/llm_client.py
- **T031** — declared artifact(s) missing/empty/invalid: code/evaluation/bias.py
- **T032b_sim** — declared artifact(s) missing/empty/invalid: code/evaluation/simulate_experts.py
- **T032d** — declared artifact(s) missing/empty/invalid: code/evaluation/run_kappa_check.py, code/evaluation/engage_4th_expert.py
- **T032c** — declared artifact(s) missing/empty/invalid: code/evaluation/rubric.py
