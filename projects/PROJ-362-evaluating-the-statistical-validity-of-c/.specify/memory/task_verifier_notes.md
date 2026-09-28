# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or ruff section in `pyproject.toml`, or corresponding CI integration scripts) are present in the provided evidence. Without these artifacts the task of configuring ruff and black cannot be confirmed as completed.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — The repository lacks the required `contracts/dataset.schema.yaml` file, and `code/data_loader.py` does not contain a `validate_qrels()` function that returns an `is_valid` flag per query and logs a warning for zero‑relevance queries. Consequently the schema‑based validation and zero‑relevance handling are not fully implemented.
