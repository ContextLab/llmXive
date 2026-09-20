# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T037** — The required script `data/download_nlcd.py` does not exist, the expected `data/raw/nlcd_2019.zip` archive is missing, and `data/metadata.yaml` contains no entry for the NLCD dataset (only a placeholder for eBird data). Consequently the task of downloading NLCD data and recording its version/date is not fulfilled.
- **T008a** — The required script `data/download_guild_source.py` does not exist, the target CSV `data/raw/guild_source.csv` is missing, and `data/metadata.yaml` lacks any entry for the guild source URL. Consequently the task’s core deliverables are absent.
- **T008b** — declared artifact(s) missing/empty/invalid: data/generate_guild_mapping.py, data/raw/guild_source.csv, data/processed/guild_mapping.csv
- **T039** — declared artifact(s) missing/empty/invalid: data/merge_and_buffer.py, data/processed/merged_observations.csv
- **T015** — The file `data/merge_and_buffer.py` does not exist, so the required `validate_schema()` function cannot be present. The test suite `tests/test_data_contract.py` is present but is truncated and only defines `test_schema_compliance`; it lacks a `test_validate_schema` unit test that checks the new function’s behavior. Both required artifacts are missing or incomplete.
- **T010** — The `tests/test_data_contract.py` file is present but the test implementation is truncated and never actually loads or validates the CSV against the schema. Moreover, the required schema file `contracts/dataset.schema.yaml` is missing entirely, so the test cannot succeed. The task’s requirement of a complete test asserting column conformity is not met.
- **T040** — The required `data/aggregate.py` file does not exist in the repository, so no code or functionality to perform the aggregation and logging is present. The task’s primary artifact is missing, making the implementation incomplete.
- **T041** — declared artifact(s) missing/empty/invalid: models/train.py, data/models/random_forest.pkl, data/models/training_metrics.json
- **T059** — declared artifact(s) missing/empty/invalid: models/stratified_permutation.py
- **T042** — declared artifact(s) missing/empty/invalid: models/evaluate.py, data/models/evaluation_results.json
- **T021** — declared artifact(s) missing/empty/invalid: models/evaluate.py
- **T023** — declared artifact(s) missing/empty/invalid: tests/test_integration.py, models/train.py, models/evaluate.py
- **T043** — declared artifact(s) missing/empty/invalid: docs/results/confusion_matrix.png
- **T044** — declared artifact(s) missing/empty/invalid: docs/results/feature_importance.png
- **T045** — declared artifact(s) missing/empty/invalid: docs/results/habitat_map.geojson
