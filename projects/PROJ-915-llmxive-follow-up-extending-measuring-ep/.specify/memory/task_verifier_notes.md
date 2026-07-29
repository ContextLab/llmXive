# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The `data/raw/medmis_subset.csv` file does not exist, and `state/artifact_hashes.yaml` contains only a placeholder instead of a real SHA‑256 hash. Moreover, the provided `code/ingestion.py` is truncated (e.g., `validate_schema` ends with a typo and never returns) and does not show the checksum computation or writing to the YAML file, so the implementation does not meet the specified requirements.
- **T015** — The provided `code/features.py` does not add a boolean `is_ratio_undefined` column (it only sets `imperative_ratio` to 0.0 when `sentence_count` is zero) and there is no logic to write a CSV with that flag. Moreover, the required output file `data/processed/features.csv` is absent. The implementation therefore fails to meet the task’s specifications.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/interim/labeled_responses.csv
