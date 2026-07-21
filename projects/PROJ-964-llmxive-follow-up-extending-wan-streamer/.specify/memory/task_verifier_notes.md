# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No directory listings or proof that the required `code/`, `code/data/`, `code/models/`, `code/inference/`, `code/evaluation/`, `code/utils/`, `code/tasks/`, and `code/tests/` folders actually exist were provided; without such evidence the `os.path.isdir` checks cannot be satisfied.
- **T003** — No evidence was provided that the directories `data/raw/`, `data/processed/`, and `data/models/` actually exist; there is no script or output showing `os.path.isdir` checks passing. The required subdirectories must be created and verified.
- **T004** — No evidence was presented showing that `state/` and `docs/` directories actually exist; there are no file listings, screenshots, or code confirming `os.path.isdir` returns True for those paths. The implementer must create the directories and provide proof (e.g., a directory tree listing or a test script that asserts their existence).
- **T005** — No evidence was provided that the `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/` directory actually exists (e.g., a screenshot, `os.path.exists` output, or a file listing). Without such proof, the required artifact cannot be confirmed.
- **T005c** — declared artifact(s) missing/empty/invalid: ruff.toml
