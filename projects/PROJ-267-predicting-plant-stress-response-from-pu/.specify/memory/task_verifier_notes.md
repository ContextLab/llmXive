# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The skeleton includes the required directories `data/raw/`, `data/processed/`, `docs/`, `results/`, the `requirements.txt`, `code/main.py` with a functional `--stage noop` option, and `docs/structure.txt`. However, the `logs/` directory is not present in the repository snapshot, violating the task’s requirement for a `logs/` folder. Adding an empty `logs/` (e.g., with a `.gitkeep`) will complete the skeleton.
- **T006** — The repository contains the required `code/utils/logger.py`, but there is no evidence that other pipeline modules import and use this logger, nor any proof that a pipeline run creates `logs/pipeline.log` with entries for dropped rows, missing columns, or errors. The missing execution logs and import usage must be provided.
