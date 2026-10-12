# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The logs/ directory is not present in the listed project tree, and there is no execution evidence showing that the commands documented in quickstart.md run successfully on a clean runner. Both are required to satisfy the task.
- **T006** — Checked `code/utils/logger.py` (exists and writes to `logs/pipeline.log`) and the verification log `code/.tasks/T006.code_utils_verify_logging.py.log` (shows the log file was created and a warning was written). However, there is no evidence that the rest of the pipeline modules import and use this logger, nor that `logs/pipeline.log` contains the required entries for dropped rows, missing columns, or raised errors after a real pipeline run. These artifacts must be added to satisfy the task.
- **T002** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
