# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The provided evidence only shows a `code/` directory; the required `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, and `state/projects/PROJ-922` directories are not present. These missing folders must be created to satisfy task T001a.
- **T001b** — The `code/requirements.txt` file is present and includes most required pins, but it does **not** contain the required `loguru==0.7.2` entry, and therefore does not fully satisfy the task specification.
- **T002a** — The required script `code/scripts/update_state.py` does not exist, and the target `state/projects/.../artifacts.yaml` is also missing, so the task’s core artifact and its intended effect are absent.
- **T038** — declared artifact(s) missing/empty/invalid: code/scripts/verify_data_source.py
- **T039** — declared artifact(s) missing/empty/invalid: code/scripts/cpu_feasibility_check.py
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.json
- **T027** — declared artifact(s) missing/empty/invalid: code/analysis/stats.py, data/interim/evaluation_scores.jsonl, data/interim/aggregated_data.csv
- **T029** — declared artifact(s) missing/empty/invalid: data/processed/glm_results.json
- **T030** — declared artifact(s) missing/empty/invalid: code/analysis/plots.py, data/processed/figures/effect_sizes.png, data/processed/figures/p_values.png, data/processed/figures/confidence_intervals.png
- **T031** — declared artifact(s) missing/empty/invalid: code/scripts/analyze.py, data/processed/final_results.csv, data/processed/analysis_report.md
- **T041** — declared artifact(s) missing/empty/invalid: code/analysis/stats.py, data/processed/glm_results.json, data/processed/convergence_report.md
- **T035** — declared artifact(s) missing/empty/invalid: tests/benchmark_batch.py
- **T037** — declared artifact(s) missing/empty/invalid: code/scripts/update_state.py, state/projects/.../artifacts.yaml, artifacts.yaml
