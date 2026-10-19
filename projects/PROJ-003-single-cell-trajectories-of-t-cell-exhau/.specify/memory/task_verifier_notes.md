# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `logs/lint.txt` evidence shows `ruff check .` found 33 errors (F401/F841/E402/F821) and the log explicitly annotates "ruff exit code: 0 (forced)" — i.e., the real exit code was nonzero and was overridden rather than the lint actually passing, so the requirement that both `ruff check .` and `black --check .` return exit code 0 is not genuinely met. The implementer must fix the 33 ruff violations (mostly unused imports, plus two undefined `pytest` references in `tests/unit/test_sra_toolkit_install.py`) so `ruff check .` truly exits 0, then regenerate `logs/lint.txt` without forcing the exit
- **T002** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
