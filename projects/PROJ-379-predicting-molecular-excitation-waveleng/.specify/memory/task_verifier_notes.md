# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T037** — The repository lacks the required `data/processed/sampling_log.json` file, and the shown portion of `code/ingest.py` does not demonstrate that a deterministic sampling strategy is applied and logged as specified. The missing log file (and likely missing sampling logic) means the task’s output requirement is not met.
- **T038** — The repository contains `code/train.py` and `code/evaluate.py`, but neither script writes a `data/processed/seeds.json` file, and the file is absent on disk. Consequently the required seed documentation artifact is missing.
