# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The collector's evidence lists only `requirements.txt`, `pyproject.toml`, and `ruff.toml`; the required `.flake8` file is missing entirely. Additionally, there is no execution evidence that `pip install -r requirements.txt`, `ruff check .`, or `black --check .` were run and passed, and `ruff.toml` places `target-version` under `[lint]` where it is not a valid key (it belongs at top level), so `ruff check .` would error.
- **T005** — Requested task execution failed; rerun successfully: code/data/curate_reference_substructures.py exit=1
