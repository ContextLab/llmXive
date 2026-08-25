# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — No `.npy` matrix file under `data/raw/` nor a `state/checksums_raw.json` file was presented. Consequently the required atomic generation and checksum recording cannot be confirmed. The implementer must provide the actual NumPy file and the JSON checksum entry.
- **T019b** — declared artifact(s) missing/empty/invalid: data/processed/single_run_results.json
- **T040a** — No `.npy` matrix files under `data/raw/sweep/` nor a `state/checksums_sweep.json` file were presented. Without these files and their SHA‑256 entries, the required grid sweep and atomic checksum recording have not been demonstrated. The implementer must provide the generated matrix files and the corresponding checksum JSON.
- **T021b** — declared artifact(s) missing/empty/invalid: data/processed/mc_results.csv, data/processed/threshold_identification.json
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_density_sweep.csv
- **T029a** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_density_sweep.csv, data/processed/sensitivity_variation.csv
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.md
- **T032a** — No updated `quickstart.md` file was provided or referenced, and there is no evidence that the documentation now contains step‑by‑step instructions for reproducing the full parameter sweep and sensitivity analysis. The required artifact is missing.
- **T033** — No updated `research.md` file or any textual evidence showing the required clarification about the "observer", the nature of the study, or the definition of "sparse noise" is provided. The implementer’s claim lacks the actual artifact needed to satisfy the task.
- **T034** — No evidence of a `research.md` file or its contents was provided, so we cannot confirm that a “Theoretical Context” section distinguishing the mathematical model from physical analogs and explicitly invoking FR‑007 was added. The required documentation artifact is missing.
- **T035** — No memory profile log `state/memory_profile_N2000.log` or any code changes were presented; thus there is no evidence that the code was refactored to stay under 7 GB RAM for N=2000 or that a memory‑profiler run was performed. The required artifact is missing.
- **T035b** — No `state/code_observation_audit.log` file was presented, and no evidence of a static analysis of the `code/` directory was provided. Without this log showing that no hard‑coded physical constants or observer assumptions remain, the task requirement is unmet. The implementer must supply the audit log containing the analysis results.
- **T036** — No `state/sweep_timing.log` file or any other evidence of the parameter sweep execution time is present; thus the required artifact is missing and the claim that the sweep completes within 6 hours cannot be verified.
