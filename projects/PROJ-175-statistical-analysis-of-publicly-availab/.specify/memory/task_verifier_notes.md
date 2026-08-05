# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: data/setup_log.json
- **T012b** — The required artifact `data/download_status.json` is missing from the repository, so the implementer could not read it or generate the amendment log as specified. No alternative file or placeholder was provided.
- **T007a** — The required schema files `dataset.schema.yaml` and `model_output.schema.yaml` are absent from `specs/001-statistical-analysis-of-recipe-data/contracts/` (the only schema file listed is missing). Additionally, the provided `validate_schema.py` script is truncated and does not demonstrate validation against the missing schemas. The deliverables are therefore not present.
- **T007b** — declared artifact(s) missing/empty/invalid: data/amendment_log.json, data/contracts/dataset.schema.yaml, schema.yaml
- **T013b** — declared artifact(s) missing/empty/invalid: data/pilot_stats.json
- **T013a** — declared artifact(s) missing/empty/invalid: data/raw/recipe1m_processed.parquet
- **T014** — The submission contains only the task description and specification; no actual pipeline code, no normalized ingredient CSV, and no generated co‑occurrence matrix or similarity scores are provided. The required artifact—a validated CSV file (or equivalent) produced by the preprocessing pipeline—is missing, so the task is not satisfied.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet
- **T016** — No code, data file, or result showing the computed cosine similarity between ingredient embeddings is present; the task description alone does not constitute the required artifact. The implementer has not provided any concrete output (e.g., a similarity matrix, script, or notebook) that fulfills T016.
