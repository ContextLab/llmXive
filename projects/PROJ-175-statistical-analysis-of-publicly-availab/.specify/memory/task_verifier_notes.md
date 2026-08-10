# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007b** — The required `specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml` file does not exist (or is empty), so the schema was not updated as specified. The implementer must create the file with the appropriate `flavor_similarity` definition based on the ratified methodology.
- **T013a** — The `recipe1m_processed.parquet` file is only a placeholder (144 bytes of dummy text) and does not contain the streamed dataset with the required schema, and the required `data/logs/recipe1m_validation.json` file is missing entirely. Both the output data and the validation log are absent, so the task is not genuinely fulfilled.
- **T014a** — No code, data file, or mapping artifact for ingredient name normalization and canonical ID mapping was provided. The task required a concrete implementation (e.g., a script or dataset) that normalizes raw ingredient strings and produces a canonical ID mapping, but the evidence contains only a placeholder comment and no tangible output.
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/functional_roles.csv
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet
- **T016b** — The amendment log indicates the task should run, but the required output file `data/processed/similarity_scores_embedding.parquet` is absent, so the embedding similarity computation was not completed. No evidence of the embeddings or parquet file is present.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/functional_roles_validated.parquet
- **T018** — The required output file `data/processed/ingredient_pairs.csv` is missing, so the pipeline never produced the final dataset with imputed similarity scores and logged exclusion counts. Without this artifact, the task’s core requirement is not satisfied.
