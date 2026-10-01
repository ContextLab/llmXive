# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `tests/`, `logs/`, `results/`) being present on disk is provided; the implementer’s claim is unsupported. The task cannot be considered complete until these folders are created (even if empty).
- **T001c** — No evidence of a `docs/` directory being present was provided; the artifact list is empty and the implementer did not supply any files or folder confirming its creation. The required directory is missing.
- **T006** — No logging configuration, script changes, or `logs/pipeline.log` file were provided; thus there is no evidence that a logging infrastructure capturing warnings has been set up as required.
- **T018** — The `code/data_ingestion/completeness.py` file is present but its content is truncated and does not show the logic that writes `results/data_completeness.json`. Moreover, the required output file `results/data_completeness.json` is missing from the repository. The task’s core deliverable – a JSON file with the calculated completeness metric – has not been produced.
