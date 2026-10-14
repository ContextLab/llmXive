# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The artifact `code/logging_config.py` exists and its content looks plausible (RotatingFileHandler to `logs/run.log`, console handler at WARNING, idempotent setup), but the only execution evidence — the recorded pytest run of `tests/unit/test_logging_config.py` — failed with exit 1 and all 5 tests erroring (`TypeError: expected str, bytes or os.PathLike object, not module` at `code/logging_config.py:91` in `setup`), and there is no evidence the task's own verification command (`lc.setup(); logging.info('test')` creating `logs/run.log`) was ever run successfully. The implementer must fix the `se
- **T004** — Requested task execution failed; rerun successfully: code/data/download.py exit=2
