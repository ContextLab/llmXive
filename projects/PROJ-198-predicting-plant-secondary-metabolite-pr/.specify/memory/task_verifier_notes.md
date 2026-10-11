# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=2
- **T003** — The repository contains `code/config.py` and the `config.env_manager` implementation, but the required `.env.example` template file is not present, and there is no execution evidence showing that sourcing it makes `config.get("NCBI_API_KEY")` and `config.get("PMDB_API_TOKEN")` return non‑empty strings. Both the template and the runtime verification are missing.
