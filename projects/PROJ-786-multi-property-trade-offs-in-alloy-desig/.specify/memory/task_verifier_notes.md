# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The spec file exists and includes the required version entries, but it does not contain the conditional pivot logic referencing HDBSCAN (or K‑Means on residuals) as required, and FR‑006 lacks the explicit 0.1 step specification. Moreover, the required output file `data/processed/spec_alignment_log.txt` is missing.
- **T004** — Checked the project root for the required `data/raw/.gitkeep` and `data/processed/.gitkeep` files; neither the directories nor the placeholder files are present in the repository. The task’s core deliverable – the directory structure with `.gitkeep` files – is missing.
- **T005** — The repository contains the `code/versioning.py` script, but the required state file `state/projects/PROJ-786-multi-property-trade-offs-in-alloy-desig.yaml` is missing and there is no evidence (e.g., execution logs or the generated YAML) showing that the script was run, produced the updated YAML, and logged hash computation. The implementer must provide a run of the script that creates/updates the YAML file and includes the corresponding console/log output.
- **T024b** — declared artifact(s) missing/empty/invalid: code/physics_bounds.py, data/processed/theoretical_bounds.json
- **T029b** — declared artifact(s) missing/empty/invalid: code/utils/ilr_transform.py
- **T031** — declared artifact(s) missing/empty/invalid: data/processed/correlation_stats.csv
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/correlation_stats.csv
- **T028** — declared artifact(s) missing/empty/invalid: tests/contract/test_visualization.py, data/results/decoupling_plot.png
