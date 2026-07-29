# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: state/template.yaml
- **T001b** — No `__init__.py` files were found in the `src/` and `tests/` directories, and a `.gitignore` file is absent (or its contents were not provided). Consequently the required files and the specific ignore rules (excluding `data/`, `__pycache__`, `*.pyc` while ensuring `state/*.yaml` is **not** ignored) are missing. The implementer must add the `__init__.py` files and create a correctly configured `.gitignore`.
- **T019a** — declared artifact(s) missing/empty/invalid: src/training/homeostasis.py
- **T020** — declared artifact(s) missing/empty/invalid: src/models/hybrid_network.py
- **T026b** — The provided `src/experiments/ablation.py` is truncated and does not contain a `run_ablation_study` function that loops through configs, trains models, computes MAE, and writes results. Moreover, the required output file `data/results/ablation_results.json` is absent. These missing pieces prevent the task from being fulfilled.
- **T027** — declared artifact(s) missing/empty/invalid: src/experiments/scaling.py, data/results/scaling_results.json
- **T028** — declared artifact(s) missing/empty/invalid: src/utils/statistics.py
- **T029** — declared artifact(s) missing/empty/invalid: src/utils/report_generator.py, data/results/cost_curve.json
- **T031** — declared artifact(s) missing/empty/invalid: src/utils/statistics.py, data/results/ablation_results.json, data/results/ablation_stats.json
