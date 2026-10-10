# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The repository contains `.ruff.toml` and a `pyproject.toml` with a Black configuration, but the required `.flake8` file is absent and there is no provided evidence (e.g., command output or logs) that `ruff --quiet .` and `black --check .` both exit with code 0. The implementer must add a valid `.flake8` configuration file and supply proof that the linting and formatting checks succeed.
- **T003** — The repository contains `code/config.py` and the `config.env_manager` implementation, but the required `.env.example` template file is not present, and there is no execution evidence showing that sourcing it makes `config.get("NCBI_API_KEY")` and `config.get("PMDB_API_TOKEN")` return non‑empty strings. Both the template and the runtime verification are missing.
