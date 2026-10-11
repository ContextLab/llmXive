# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The logger module `code/utils/logger.py` exists and looks functional, but there is no evidence that `logs/pipeline.log` was ever created — the only execution record (`--stage noop`) shows console output only, and no log file artifact is present in the evidence. Additionally, nothing demonstrates that pipeline modules actually import/use this logger, nor that the log contains entries for dropped rows, missing columns, or raised errors as the verification criterion requires.
- **T002** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
