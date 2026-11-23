# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked the top‑level project directory `projects/PROJ-484-the-impact-of-visual-attention-on-recall/` and found the required subfolders `code/`, `data/` and `tests/`. Inside `data/` the `raw/` folder exists, but `processed/` is absent, and there is no `artifacts/` directory at all (hence missing `artifacts/figures` and `artifacts/logs`). The required directory structure is therefore incomplete.
- **T001b** — The README.md file is present and meets the content requirements, but the required `.gitignore` file is missing from the project root (or its contents are not provided). The task is not fully satisfied until a `.gitignore` with the specified exclusions is added.
- **T002** — The `requirements.txt` file exists, but most listed packages (pandas, numpy, scipy, matplotlib, seaborn, tqdm, huggingface_hub) are not version‑pinned, violating the “Pin versions where possible” requirement. Version specifiers need to be added for these dependencies.
- **T002b** — declared artifact(s) missing/empty/invalid: code/venv/pyvenv.cfg
- **T004** — The `data/processed/` directory does not exist, and there is no evidence of the required `artifacts/figures/` and `artifacts/logs/` directories. The task demands all four directories be created; only `data/raw/` is present.
- **T005** — The provided `logging_config.py` does not create a rotating file handler at the required path (`artifacts/logs/app.log`) nor enforce DEBUG level, and its JSON formatter outputs `logger` instead of the required `module` field. The implementation therefore does not satisfy the task specifications.
- **T028** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py
- **T030** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py
- **T026** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py
- **T027** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py
- **T032** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py
- **T064** — declared artifact(s) missing/empty/invalid: projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py
