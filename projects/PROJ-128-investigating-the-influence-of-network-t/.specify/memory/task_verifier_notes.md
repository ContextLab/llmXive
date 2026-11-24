# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The `data/` directory correctly contains the required subfolders (raw, derived, logs), but both required schema files `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` are reported as missing. Without these files the task’s contract‑setup requirement is not fulfilled.
- **T012** — The provided `tests/unit/test_structural.py` imports and tests functions from `preprocess.structural`, not the public API in `code/structural.py`. It checks for keys like `average_clustering_coefficient` and `num_nodes` that `code.structural.calculate_graph_metrics` does not return, so the unit test does not verify the graph‑metric calculation of `code/structural.py` as required. A proper test should import `code.structural` and assert the presence and correctness of its returned keys (`global_efficiency`, `clustering`, `modularity`).
- **T015b** — declared artifact(s) missing/empty/invalid: code/structural.py, data/derived/structural_density_sensitivity.csv
- **T016** — declared artifact(s) missing/empty/invalid: code/functional.py, data/derived/loo_centroids_all_subjects.npz, data/logs/methodology_deviations.json, data/derived/state_assignments_per_subject.csv
- **T017** — declared artifact(s) missing/empty/invalid: code/functional.py, data/derived/loo_centroids_all_subjects.npz, data/derived/state_assignments.csv, data/derived/dynamic_metrics.csv, data/logs/exclusion_log.json
- **T001a** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
- **T024** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T025** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T026** — declared artifact(s) missing/empty/invalid: code/correlation.py
- **T027** — declared artifact(s) missing/empty/invalid: data/derived/correlation_results.csv
- **T042b** — declared artifact(s) missing/empty/invalid: data/derived/tractography_sensitivity_metrics.csv
- **T060** — declared artifact(s) missing/empty/invalid: code/structural.py, code/functional.py, data/logs/data_source_verification.json
- **T061** — declared artifact(s) missing/empty/invalid: data/logs/resource_budget_estimate.json
- **T063** — declared artifact(s) missing/empty/invalid: docs/constitution_audit.md
