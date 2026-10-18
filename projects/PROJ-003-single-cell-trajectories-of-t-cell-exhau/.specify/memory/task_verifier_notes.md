# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The layout, `data/results/.gitkeep`, and `quickstart.md` (with `python -m code.run_all` and a usage example) are present, and unit tests pass. However, `logs/lint.txt` shows `ruff check .` actually FAILED — it could not parse `.ruff.toml` ("unknown field `line-length`" at line 18) — and the setup script merely reported "ruff exit code: 0" by masking the failure, so the requirement that ruff genuinely pass with exit code 0 is not met. Fix `.ruff.toml` (e.g., move `line-length` under `[tool.ruff]`/`[lint]` correctly or use `pyproject.toml`) so `ruff check .` truly exits 0, then regenerate `logs/
- **T002** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
