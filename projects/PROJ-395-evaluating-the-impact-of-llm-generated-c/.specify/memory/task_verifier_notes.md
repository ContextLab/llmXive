# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The response contains only the task description and specifications but provides no evidence (e.g., a directory listing, screenshots, or file paths) that the `projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/` directory and its `data/`, `code/`, `tests/`, `state/` subdirectories actually exist. Without such artifacts, we cannot confirm the required structure was created.
- **T002** — No artifact such as a created Python 3.11 virtual environment, a `requirements.txt`/`pyproject.toml`, or installation logs was provided. Without any evidence of the environment being initialized or dependencies installed, the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) are present, and the only evidence supplied relates to memory‑profiling user stories, not to configuring ruff/flake8/black. The required artifacts are missing.
- **T004** — No directory structure (`data/raw/`, `data/processed/`, `state/`, `code/`) is presented in the provided artifacts; without visible evidence of these folders being created, the task requirement is not satisfied. The implementer must add the directory tree (even if empty) to the repository.
- **T008** — declared artifact(s) missing/empty/invalid: code/download.py
- **T009** — The provided evidence contains only a feature specification for memory‑profiling and statistical analysis; there is no `state/` directory, no code implementing versioning logic, and no functionality that computes or records SHA‑256 hashes for artifacts. Consequently, the required artifact is missing.
- **T010** — The required `code/download.py` file does not exist, and consequently no unit test for it can be present. The missing module means the task’s core artifact is absent, so the requirement is not satisfied.
- **T012** — declared artifact(s) missing/empty/invalid: code/generate.py
