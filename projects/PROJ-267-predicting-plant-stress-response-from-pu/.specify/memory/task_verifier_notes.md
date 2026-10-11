# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The skeleton directories, `requirements.txt`, `code/main.py` with a `--stage noop` option, and `docs/structure.txt` are present and contain appropriate content. However, there is no execution evidence showing that `python -m code.main --stage noop` actually exits 0, nor any proof that the commands documented in `quickstart.md` run successfully on a clean runner. Execution logs or test results are required to satisfy those verification steps.
- **T006** — The repository contains a `code/utils/logger.py` that correctly configures a logger writing to `logs/pipeline.log`, and a verification script reports success, but there is no actual `logs/pipeline.log` file shown nor evidence that other pipeline modules import and use this logger. Without the real log file containing the required INFO/WARN entries and import usage across the codebase, the task is not fully satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
