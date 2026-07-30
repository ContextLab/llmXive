# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The required file `specs/contracts/model_output.schema.yaml` does not exist (the only mentioned `schema.yaml` is missing), so the schema with the specified columns was never provided. The task needs the creation of that YAML file containing the listed fields.
- **T018** — The provided `src/main.py` imports the validation utilities but never actually calls them, and the script ends before saving a validated dataset to `data/processed/games.parquet`. Moreover, the expected `games.parquet` file is absent from the repository. The task’s requirement—to run schema validation on the generated dataset and then write the validated data to the specified Parquet file—is therefore not fulfilled.
- **T027** — declared artifact(s) missing/empty/invalid: data/results/model_metrics.json, schema.yaml
- **T033** — declared artifact(s) missing/empty/invalid: data/results/diagnostics.json
- **T034** — No updated `README.md` or `quickstart.md` files are present in the provided evidence; the only artifacts shown relate to statistical analysis specifications, not documentation changes. The required documentation updates are missing.
- **T035** — No code, commit diff, or refactoring report was provided; the only evidence is the original feature specification, which does not demonstrate any cleanup or refactoring work. The required artifact (cleaned/refactored code) is missing.
- **T036** — No artifact showing that RAM usage was measured and kept below 7 GB is present, nor any code or documentation indicating that data sampling was implemented to achieve this limit. Without performance benchmarks or sampling logic, the task’s requirement is not satisfied.
- **T037** — No `tests/unit/` directory or any unit test files were provided as evidence, so the required additional unit tests are missing. The task cannot be considered complete without actual test artifacts in the specified location.
- **T038** — No artifact showing that the `quickstart.md` file was validated (e.g., validation script output, logs, or a corrected `quickstart.md`) is present. The claim lacks any evidence that the required validation step was performed.
