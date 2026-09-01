# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory at the repository root is provided; the artifact list is empty, so the required directory has not been demonstrated as existing. The implementer must add the `code/` folder (non‑empty) to satisfy the task.
- **T001b** — No evidence was provided that a `data/` directory exists at the repository root; the claim lacks any artifact (e.g., directory listing, screenshot, or file) confirming its creation. The required directory is missing from the supplied information.
- **T001c** — No artifact showing a `tests/` directory at the repository root was provided; without evidence of the directory’s existence, the requirement cannot be confirmed as satisfied. The implementer must add proof (e.g., a directory listing or a file inside `tests/`).
- **T001d** — No evidence of a `paper/` directory at the repository root is provided; the artifact list is empty, so the required directory has not been demonstrated as existing. The implementer must add the `paper/` folder to satisfy the task.
- **T003** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — The required artifact `tests/unit/test_static_analysis.py` does not exist in the repository, so no unit test for metric calculation is present. The task cannot be considered completed until this file is added with appropriate tests.
- **T014** — The provided `code/data/processor.py` is truncated (ends with an incomplete `except Exception as` block) and does not show the final steps that write the JSON file. Moreover, the required output `data/processed/raw_metrics.json` is absent from the repository. The implementation therefore does not demonstrably fulfill the saving requirement.
- **T017** — declared artifact(s) missing/empty/invalid: tests/unit/test_baseline.py
- **T018** — The required artifact `tests/integration/test_refactoring_pipeline.py` does not exist in the repository, so the integration test for the refactoring batch processing is missing. The task cannot be considered complete until this file is created with appropriate test code.
- **T022** — The repository contains a `code/llm/pipeline.py` file, but it is truncated and does not show the final steps that write the results to `data/processed/refactoring_results.json`. Moreover, the required output file `data/processed/refactoring_results.json` is absent from the project. Without this saved JSON of deltas, the task’s core requirement is not fulfilled.
