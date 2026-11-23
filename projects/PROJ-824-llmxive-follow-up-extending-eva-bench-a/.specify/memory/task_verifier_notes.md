# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The artifact `code/logging_config.py` exists and its content plausibly implements rotation, a WARNING console handler, and the `logs/run.log` default, but the only execution evidence (the pytest log for `tests/unit/test_logging_config.py`) shows all 7 tests ERRORING because a fixture passes a module as `log_file` and `setup()` raises `TypeError`. The current code still contains that same `TypeError` guard, so there is no evidence the tests were ever re-run and passing after any fix, nor any evidence the verification command (`lc.setup(); logging.info('test')` creating `logs/run.log`) was actua
- **T004** — Requested task execution failed; rerun successfully: code/data/download.py exit=2
