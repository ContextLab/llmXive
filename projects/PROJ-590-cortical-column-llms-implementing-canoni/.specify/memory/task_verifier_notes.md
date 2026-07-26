# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory tree or listing of the required folders (`src/models`, `src/data`, `src/training`, `src/experiments`, `src/utils`, `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state`) is provided; without concrete evidence the task is not satisfied. The implementer must create the directories and show a file‑system listing or similar proof.
- **T001b** — No `__init__.py` files are shown in any `src/` or `tests/` directories, and no `.gitignore` file with the required exclusion patterns is present in the provided evidence. The implementer must add the missing `__init__.py` files and create a `.gitignore` that excludes `data/`, `__pycache__/`, `*.pyc`, and `state/*.yaml` (except the template).
- **T003a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T008a** — declared artifact(s) missing/empty/invalid: src/training/homeostasis.py
- **T008b** — declared artifact(s) missing/empty/invalid: src/training/homeostasis.py, data/logs/gradient_norms.json
- **T019a** — declared artifact(s) missing/empty/invalid: src/training/homeostasis.py
- **T020** — declared artifact(s) missing/empty/invalid: src/models/hybrid_network.py
- **T032** — declared artifact(s) missing/empty/invalid: src/utils/statistics.py, data/results/gradient_stability.json
- **T026a** — declared artifact(s) missing/empty/invalid: src/experiments/ablation.py, data/configs/ablation_configs.json
- **T026b** — declared artifact(s) missing/empty/invalid: src/experiments/ablation.py, data/results/ablation_results.json
- **T027** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py
- **T028** — declared artifact(s) missing/empty/invalid: src/utils/statistics.py
- **T029** — declared artifact(s) missing/empty/invalid: src/utils/report_generator.py, data/results/cost_curve.json, data/results/cost_curve.png
- **T031** — declared artifact(s) missing/empty/invalid: src/utils/statistics.py, data/results/ablation_results.json, data/results/ablation_stats.json
