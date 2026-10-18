# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `code/models/` sub‑directory is reported as missing, and there is no execution evidence showing that `python -m code.main --phase init` actually prints “Initialization complete” as the verification step demands.
- **T002** — The required `data/raw/coco_captions.parquet` file is missing (the provided script writes a CSV instead of a Parquet file), and the expected preprocessing script `code/data/preprocess_coco.py` does not exist (the log shows a different `preprocess.py` was run). Consequently the task’s first two steps are not satisfied, even though the diverse prompts script and CSV output are present.
