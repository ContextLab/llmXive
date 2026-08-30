# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No `__init__.py` files are present in any of the required package directories (`code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`). The implementer provided only a feature specification and no filesystem artifacts, so the task requirement is not satisfied.
- **T001e** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or any evidence of them being set up were presented. The claim lacks the required artifacts to demonstrate that ruff/flake8 and Black have been configured for the project.
- **T003** — The required `code/data/ground_truth.json` file does not exist, and the provided `synthetic_pop.py` generates only 1,000 populations of size 1,000 (variables `N_SIM` and `POPULATION_SIZE`) instead of the required 1,000,000‑sized synthetic populations. Both the output artifact and the generation specifications are missing/incorrect.
