# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The recorded execution of `pytest tests/quickstart_test.py` timed out after 600 s with exit code -1 (ok=False), so the task's stated verification criterion is not met — there is no evidence the quickstart command or tests pass. Additionally, `code/generation.py` is an explicit placeholder that returns a hard-coded string without invoking any model (the task requires invoking the generation module, and the output file is a self-declared "[Placeholder generation...]"), and `quickstart.md` contains malformed shell commands (`python -m venv.venv`, `source.venv/bin/activate` — missing spaces), so t
- **T003** — Requested task execution failed; rerun successfully: code/data_extraction.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/gold_annotation.py exit=1
