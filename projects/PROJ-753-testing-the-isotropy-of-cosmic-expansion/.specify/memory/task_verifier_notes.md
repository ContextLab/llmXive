# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `pyproject.toml` is correct, but `scripts/lint.sh` does not run `black --check . && ruff .` as required—it runs `black .` (reformat) and forces Ruff to exit zero with `--exit-zero`. The script must be changed to the exact command sequence specified.
- **T004** — Requested task execution failed; rerun successfully: code/download_pantheon.py exit=1
