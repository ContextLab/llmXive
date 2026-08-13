# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: data/logs/dir_tree.json
- **T001b** — The required artifact `data/logs/core_files.json` is missing, so the verification step is not satisfied. Without this file listing the created core files and their checksums, the task cannot be considered complete.
- **T003** — The `pyproject.toml` correctly contains the `ruff` and `black` configuration, but the required artifact `data/logs/linting_config.json` does not exist, so the verification step is missing. The task remains incomplete until this log file is generated and contains the validation output.
- **T004a** — The required artifact `data/logs/model_selection.json` does not exist, so the model selection was neither performed nor logged as specified. The task’s core requirement—deterministically selecting a model and recording it in the JSON log—is unmet. The implementer must create the log file with the selected model entry.
- **T010a** — No evidence of the required `data/raw/vuldeepecker_*` files is provided; the response contains only task description and project specifications, with no actual downloaded dataset or file listings to verify that the VulDeePecker Python dataset was saved to `data/raw/`. The implementer must supply the downloaded files (or a directory listing) to satisfy the task definition.
- **T011** — declared artifact(s) missing/empty/invalid: data/raw/checksums.json
- **T011b** — declared artifact(s) missing/empty/invalid: data/raw/checksums.json
