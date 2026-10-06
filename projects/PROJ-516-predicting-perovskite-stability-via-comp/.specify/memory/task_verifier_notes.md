# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: code/state_manager.py, state/project_state.yaml
- **T013b** — No `metadata.json` file (or a diff showing the added `precision_from_registry` flag and updated `precision_source` fields) was provided, nor any verification output confirming that the provenance information was correctly merged for every record. Consequently the required artifact is missing.
- **T061** — The repository contains `code/utils/uncertainty_calculator.py`, but the file is truncated and does not show any logic that reads `data/raw/perovskites_merged.csv`, writes `data/processed/descriptors_uncertainty.csv`, or creates `data/processed/exclusion_log.csv`. Moreover, the required input CSV (`data/raw/perovskites_merged.csv`) and the two output CSVs are absent, so the task’s core functionality cannot be verified or executed.
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_features.csv
