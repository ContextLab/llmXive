# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — declared artifact(s) missing/empty/invalid: data/logs/simulation_run.log
- **T020a** — The repository contains `code/analysis/threshold_sweep.py`, but the required output artifacts `data/processed/mc_results.csv` and `data/processed/convergence_data.json` are absent. Without these files, the orchestrator does not fulfill the task’s core deliverable of producing the processed results and convergence data. The implementer must ensure the script runs the sweep and writes the two files in the specified locations.
- **T020b** — declared artifact(s) missing/empty/invalid: data/processed/mc_results.csv, data/processed/validated_sweep_results.csv
- **T021c** — declared artifact(s) missing/empty/invalid: data/processed/validated_sweep_results.csv, data/processed/threshold_identification.json
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/critical_threshold_report.json
- **T022c** — declared artifact(s) missing/empty/invalid: data/processed/threshold_fit_params.json
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/threshold_sweep_results.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/figures/outlier_probability_vs_theta.png
- **T031** — declared artifact(s) missing/empty/invalid: data/logs/edge_case_rank0.log
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_density_sweep.csv
- **T028b** — The required file `data/processed/sensitivity_metadata.json` is missing, so no `PerturbationConfig` records (including rank and support density) have been instantiated or saved. The task’s core artifact is absent.
- **T029a** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_density_sweep.csv, data/processed/sensitivity_variation.csv
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.md
- **T032a** — No updated `quickstart.md` file was provided or referenced, and there is no evidence that the documentation now contains step‑by‑step instructions for reproducing the full parameter sweep and sensitivity analysis. The required artifact is missing.
- **T033** — No updated `research.md` file or any textual evidence showing the required clarification about the "observer", the nature of the study, or the definition of "sparse noise" is provided. The implementer’s claim lacks the actual artifact needed to satisfy the task.
