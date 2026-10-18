# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `data/results/` directory with `.gitkeep` and `quickstart.md` (containing `python -m code.run_all` and a usage example) do exist, but the lint requirement fails: `logs/lint.txt` shows `ruff check .` found 33 errors (F401/F841/E402/F821), and the log explicitly says "ruff exit code: 0 (forced)" — the setup script masked the real non-zero exit code instead of actually passing. To fix: clean up the unused imports/undefined `pytest` names (or configure ruff appropriately) so `ruff check .` genuinely exits 0, then regenerate `logs/lint.txt` without forcing the exit code.
- **T002** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
