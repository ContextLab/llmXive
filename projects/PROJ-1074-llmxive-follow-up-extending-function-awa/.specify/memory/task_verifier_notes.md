# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (e.g., `code/data`, `data/raw/gsm8k`, `docs/`, etc.) is provided; the implementer did not supply any artifact confirming the project structure was created.
- **T003** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T004** — No evidence of the required `data/raw/gsm8k` and `data/raw/logiqa` directories (or any files within them) is present; the implementer provided no artifacts showing the directory structure was created. The task remains undone until those directories exist in the repository.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T027** — No `pytorch_model.bin` or `config.json` were found in `data/artifacts/baseline_model/`; the required baseline model files are missing, so the task is not satisfied.
- **T011** — The provided test file is truncated and does not show a `test_dataset_schema_validates_jsonl` function, and the required `dataset.schema.yaml` file is missing, so the test cannot actually validate any JSONL against the schema. The necessary schema artifact must be added and the test function confirmed.
- **T014** — The repository contains a `convert_to_pseudo_code.py` script, but the shown code never writes any data to `data/processed/intermediate_steps.jsonl`, and that file is absent from the project. Consequently the required artifact is missing, so the task is not fulfilled.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/dependency_graphs.json
- **T017** — No `convert_to_pseudo_code.py` file (or its contents) was provided, and there is no evidence that a topological‑sort check was added to reject cyclic examples. The required code change and its behavior cannot be verified.
- **T018c** — The `code/data/track_intermediate_caches.py` script is present, but the required output file `data/processed/intermediate_caches.json` does not exist, so the cache‑tracking mechanism has not produced the logged data as specified.
