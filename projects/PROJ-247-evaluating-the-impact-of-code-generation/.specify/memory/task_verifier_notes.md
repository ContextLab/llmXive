# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The collector-confirmed artifacts cover `code/requirements.txt` (all required pinned packages present), `code/utils/models.py`, and the quickstart (resolved at `specs/001-evaluating-the-impact-of-code-generation/quickstart.md`), but there is no evidence of the required logging configuration or a `.env.example` file containing `GITHUB_TOKEN`, `DATA_PATH`, and `LOG_PATH` — the quickstart even instructs `cp .env.example .env`, yet no such file appears among the artifacts. The implementer must add the logging config and `.env.example` (with those three variables) to complete T001.
- **T003** — Requested task execution failed; rerun successfully: code/03_code_block_extraction.py exit=1
