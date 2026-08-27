# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — The repository contains a partially‑implemented `code/src/stats/sensitivity.py`, but the file is truncated and does not include logic to write the required CSV. Moreover, the expected output file `data/processed/sensitivity_analysis.csv` is absent. The task’s core deliverable – a CSV with `threshold` and `robustness_metric` columns – is therefore not present.
- **T035b** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv, data/processed/robustness_report.json
- **T050** — The `streaming_flow_processor` function is only partially shown and ends abruptly, indicating it is not fully implemented. Additionally, the required output file `data/processed/motion_labels.json` does not exist. Both the functional implementation and the incremental JSON writing are missing.
- **T037** — declared artifact(s) missing/empty/invalid: data/processed/fidelity_report.json
- **T038** — The required `data/processed/manifest.json` file does not exist, and the corresponding state file `state/projects/PROJ-829-llmxive-follow-up-extending-fashionchame.yaml` is also missing, meaning the manifest generation and state update steps were never performed. The implementer must run the provided scripts to create these artifacts.
