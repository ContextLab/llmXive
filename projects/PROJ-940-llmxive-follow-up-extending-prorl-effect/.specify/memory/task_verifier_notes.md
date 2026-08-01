# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or `__init__.py` files were presented as evidence; without a visible listing of `src/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `results/` and the required empty `__init__.py` files, we cannot confirm the project structure was actually created. The implementer must provide a file‑system snapshot or listing showing these directories and files.
- **T005** — No directory structure or `.gitkeep` files were presented; the response contains only the task description and no tangible artifacts confirming that `data/raw/`, `data/processed/`, and `results/` exist with placeholder files. The required files are missing.
- **T021** — declared artifact(s) missing/empty/invalid: src/evaluator.py
- **T022** — declared artifact(s) missing/empty/invalid: src/evaluator.py
- **T023** — declared artifact(s) missing/empty/invalid: src/evaluator.py
- **T024** — The provided `src/main.py` exists but does not produce the required output files; `results/greedy_paths.json`, `results/greedy_rectified_paths.json`, and `results/beam_rectified_paths.json` are missing. Consequently the evaluation pipeline on the full test set has not been executed as specified.
- **T025** — The provided `src/main.py` does not contain any logic that computes the mean absolute difference between rectified and raw scores or writes a `results/sc005_status.json` file, and the required `results/sc005_status.json` file is absent from the repository. Both the validation implementation and the output artifact are missing.
- **T025b** — declared artifact(s) missing/empty/invalid: src/evaluator.py, results/greedy_paths.json, results/greedy_rectified_paths.json, results/metrics_comparison.json
- **T028** — declared artifact(s) missing/empty/invalid: src/stats.py
- **T028b** — declared artifact(s) missing/empty/invalid: src/stats.py, results/statistical_significance.json
