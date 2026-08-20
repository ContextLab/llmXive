# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the directory tree `projects/PROJ-455-predicting-plant-stress-resilience/` with the listed subfolders actually exists; the response contains only the task description and specifications, not the required filesystem artifacts. The implementer must create and show the populated project structure.
- **T004** — No `contracts/` directory or schema definition files are present in the provided evidence; the task required defining data schemas in that location, which is missing.
- **T007** — declared artifact(s) missing/empty/invalid: code/data/generator.py
- **T008** — The `MockAdapter` class is present, but it builds a hard‑coded DataFrame instead of invoking a synthetic generator, and the required `dataset.schema.yaml` file is missing, so we cannot confirm the DataFrame matches the schema. Both the generator call and the schema reference are absent.
- **T022** — The repository lacks the required `model_result.schema.yaml` file, and the `train_random_forest` implementation does not compute or return real cross‑validation metrics (it uses a placeholder `metric_value: 0.0` and no CV logic). Consequently the function’s output does not meet the schema‑compliant metric requirement.
