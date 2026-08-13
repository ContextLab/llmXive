# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project directory `projects/PROJ-546-predicting-molecular-properties-from-qua/` or any of its subfolders/files is present in the provided evidence, so the required project structure has not been created. The implementer must add the full directory hierarchy (e.g., `data/`, `logs/`, `reports/`, `idea/`, etc.) as specified in the implementation plan.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` entries for ruff/black, `.ruff.toml`, `.pre-commit-config.yaml`, or similar) are present, nor any documentation or scripts showing that ruff and black have been set up for the project. Consequently, the required artifact for task T003 is missing.
- **T004** — declared artifact(s) missing/empty/invalid: code/fetch_data.py
- **T011** — The test file `tests/test_fetch.py` is present but appears truncated (the `test_main_with_mocked_download` function ends abruptly) and cannot import the required module because `code/fetch_data.py` is missing entirely, so the contract test cannot actually run or verify Zenodo fetching. Both the implementation file and a complete, runnable test are needed.
