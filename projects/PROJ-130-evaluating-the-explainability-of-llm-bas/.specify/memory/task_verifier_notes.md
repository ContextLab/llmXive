# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No directory listings or file contents were provided, so we cannot confirm that `explanations/.gitkeep`, `state/.gitkeep`, and `tests/.gitkeep` actually exist. The required evidence (e.g., output of `ls explanations/` showing the .gitkeep file) is missing.
- **T005** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T012** — The claim provides no files, code, or documentation under `tests/contract/`, nor any implementation of a contract test framework that validates YAML schemas. Without the required test suite or framework artifacts, the task is not satisfied. The next implementer must add a `tests/contract/` directory containing test code that loads the project's YAML schemas and asserts conformity of relevant data structures.
- **T014** — No logging configuration files, code snippets, or documentation were provided to demonstrate that edge cases (invalid patches, timeouts, missing rationales) are being recorded. The required artifact—an implemented logging infrastructure—is missing.
