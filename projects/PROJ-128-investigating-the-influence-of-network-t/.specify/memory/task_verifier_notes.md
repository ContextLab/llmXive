# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — `code/config.py` exists and defines most hyperparameters, but it deviates from the task's explicit requirements: `WINDOW_LENGTH_VALIDATION = 20` is a scalar, not the required list `[20]`; the required `BASELINE_DENSITY` variable is absent (it's named `DENSITY_THRESHOLD_BASELINE`); and `DENSITY_THRESHOLD_VARIATIONS = [0.10, 0.15, 0.20]` uses a ±0.05 absolute offset rather than the FR-008-specified ±5% perturbation of the baseline (which for 0.15 would be ~[0.1425, 0.15, 0.1575], or the baseline should be 0.1 with [0.095, 0.1, 0.105]).
- **T005** — The only artifact on disk is `code/__init__.py` (a package marker), but the task also requires data loading utilities for HCP OpenNeuro dMRI/fMRI data, and no such module (e.g., a loader script with functions for reading/connectivity/time-series data) exists anywhere in the project. The implementer completed only half the task; a non-empty data-loading module with real HCP data-loading logic must be added.
- **T006** — declared artifact(s) missing/empty/invalid: code/structural.py
- **T007** — declared artifact(s) missing/empty/invalid: code/functional.py
- **T008** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T015b** — declared artifact(s) missing/empty/invalid: code/structural.py, data/derived/structural_density_sensitivity.csv
- **T016** — declared artifact(s) missing/empty/invalid: code/functional.py, data/derived/loo_centroids_all_subjects.npz, data/logs/methodology_deviations.json, data/derived/state_assignments_per_subject.csv
- **T017** — declared artifact(s) missing/empty/invalid: code/functional.py, data/derived/loo_centroids_all_subjects.npz, data/derived/state_assignments.csv, data/derived/dynamic_metrics.csv, data/logs/exclusion_log.json
- **T001a** — declared artifact(s) missing/empty/invalid: data/logs/exclusion_log.json, data/raw/verified_manifest.json
- **T024** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T025** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T026** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T027** — declared artifact(s) missing/empty/invalid: data/derived/correlation_results.csv
- **T042b** — declared artifact(s) missing/empty/invalid: data/derived/tractography_sensitivity_metrics.csv
- **T060** — declared artifact(s) missing/empty/invalid: code/structural.py, code/functional.py, data/logs/data_source_verification.json
- **T061** — declared artifact(s) missing/empty/invalid: data/logs/resource_budget_estimate.json
- **T063** — declared artifact(s) missing/empty/invalid: docs/constitution_audit.md
