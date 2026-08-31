# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the directory tree `projects/PROJ-455-predicting-plant-stress-resilience/` with the listed subfolders actually exists; the response contains only the task description and specifications, not the required filesystem artifacts. The implementer must create and show the populated project structure.
- **T004** — No `contracts/` directory or schema definition files are present in the provided evidence; the task required defining data schemas in that location, which is missing.
- **T008** — The `MockAdapter` class is present and calls the synthetic generator, but the required `dataset.schema.yaml` file is missing, so we cannot verify that the returned DataFrame conforms to the specified schema. Add the `schema.yaml` (or place it at the expected path) and ensure the mock data columns match it.
- **T022** — The repository lacks the required `model_result.schema.yaml` file, and the `train_random_forest` implementation contains a bug (it returns an undefined variable `metric` instead of the constructed `metrics` dict). Both the schema artifact and a correct return value are missing, so the task is not genuinely fulfilled.
- **T038** — declared artifact(s) missing/empty/invalid: code/analysis/sensitivity.py
- **T041** — No evidence of a `README.md` file containing the required sections (Installation, Data Generation (Synthetic), Execution Command, Expected Output) was provided; the artifact is missing or not shown, so the task cannot be confirmed as completed.
