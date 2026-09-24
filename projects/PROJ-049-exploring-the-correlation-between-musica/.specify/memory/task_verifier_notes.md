# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — The `code/power_analysis.py` script is truncated and contains undefined variables (e.g., `power_`), so it cannot run to produce a sample size. Moreover, the required output files `results/power_analysis.txt` and the state YAML file are absent, and no updates to `research.md` are present. The task’s core deliverables are therefore missing.
- **T000b** — No `research.md` file was presented, and no evidence of its contents (dataset URLs, “Real‑First” paragraph, or the sample size from T000a) was provided. The required artifact is missing, so the task is not satisfied.
- **T001a** — No evidence of the required directories (`data/raw/`, `data/processed/`, `code/`, `tests/`, `results/`, `logs/`) being created or of any assertions checking their existence is provided. The implementer did not supply a script, command output, or filesystem snapshot confirming the directory structure.
- **T001b** — No evidence was presented showing that empty `__init__.py` files actually exist in the `code/` and `tests/` directories; without file listings or contents we cannot verify the required artifacts are present. The implementer must add and show the two empty `__init__.py` files.
