# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004c** — The `code/config.py` file contains only static dataclass defaults and no runtime logic to read `data/processed/config.yaml`, and the required `data/processed/config.yaml` file is absent from the repository. Consequently, the configuration loader and deferred parameters are not implemented.
- **T020** — The `loader.py` file is present but its content (truncated) shows only utility functions; there is no implementation of `datasets.load_dataset(..., streaming=True)`, on‑the‑fly filtering, recovery strategy, parquet generation, or the watchdog logic. Moreover, the required output file `data/processed/subtle_cue_subset.parquet` is missing. The task’s core requirements are therefore not satisfied.
