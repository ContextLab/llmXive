# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `requirements.txt` is missing the required `nilearn` and `networkx` packages and does not pin any versions (e.g., `numpy==1.26.0`). It also includes unrelated packages (matplotlib, seaborn, pytest, datasets, nibabel) that were not requested. The task’s requirement for a fully pinned list of the specified dependencies is therefore not met.
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
