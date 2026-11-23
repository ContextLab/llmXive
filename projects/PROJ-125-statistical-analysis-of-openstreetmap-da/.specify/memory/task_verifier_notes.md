# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T037** — No linting reports, fixed code files, or verification logs are provided; there is no evidence that ruff/black were run on the `code/` directory or that any errors remain. The required artifact (linting output or clean code) is missing.
- **T038b** — No `config.py` file or evidence of a tuned `MAX_BLOCKS` value is provided, and there is no proof that peak memory usage has been verified to stay below the 6 GB threshold. The required artifact is missing.
- **T039** — I looked for new unit‑test files under `tests/unit/` that target `config.py` and `utils/memory.py`. No such test modules (e.g., `test_config.py` or `test_memory.py`) are present, nor any evidence of added test code. The required unit tests are missing, so the task is not satisfied.
- **T041** — No evidence of a quickstart.md file or any validation results is present; the implementer provided no artifact (e.g., the markdown file, validation script output, or logs) to demonstrate that the quickstart documentation was actually checked. Consequently the task requirement cannot be confirmed as satisfied.
- **T042** — No updated `spec.md` file is provided or shown; without the actual document we cannot verify that the fallback strategy `OLS_DEGRADED` has been documented as the governing rule for memory constraints. The required artifact is missing.
