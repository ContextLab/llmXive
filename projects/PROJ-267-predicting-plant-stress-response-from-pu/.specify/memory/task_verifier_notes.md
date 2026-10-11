# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The skeleton directories, `requirements.txt`, `code/main.py` with a `--stage noop` option, and `docs/structure.txt` are present and correctly populated. However, there is no execution evidence showing that `python -m code.main --stage noop` actually runs and exits with status 0 (or that the quickstart command runs successfully), which is a required part of the task. A test run log or similar proof is needed.
- **T006** — The repository contains the required `code/utils/logger.py`, but there is no evidence that other pipeline modules import and use this logger, nor any proof that a pipeline run creates `logs/pipeline.log` with entries for dropped rows, missing columns, or errors. The missing execution logs and import usage must be provided.
