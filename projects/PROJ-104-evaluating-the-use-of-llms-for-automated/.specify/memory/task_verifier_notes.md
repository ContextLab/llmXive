# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quick‑start guide omits any instruction for setting `GITHUB_TOKEN` and describes only a “smoke‑test” that uses a hard‑coded commit pair rather than a real 5‑sample subset downloaded by the data‑extraction script. Moreover, `tests/test_quickstart.py` calls `run_pipeline.main` directly instead of invoking the command via `subprocess`, and it does not capture stdout as required. These omissions mean the task’s specifications are not fully met.
- **T003** — Requested task execution failed; rerun successfully: code/data_extraction.py exit=1
