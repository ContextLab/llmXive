# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure was presented or listed; the claim that `projects/PROJ-202-predicting-the-impact-of-molecular-chira/` exists is unsupported by any provided artifact. The required folder hierarchy is missing from the evidence.
- **T001c** — No evidence of `.gitkeep` files being present in `data/raw`, `data/processed`, `data/interim`, `code`, or `tests` was provided; the artifact list is empty, so the requirement is not satisfied. The implementer must add a `.gitkeep` file to each of those directories.
- **T003** — No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with black settings) are present in the provided evidence, so the requirement to configure ruff/flake8 and black is not satisfied.
- **T004** — No evidence of the required `data/raw`, `data/processed`, and `data/interim` directories (or accompanying `.gitkeep` files) was provided; the implementer did not supply any artifact showing the directory structure.
- **T007** — declared artifact(s) missing/empty/invalid: code/models/data_models.py
- **T008** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T009** — No `.env` file, configuration-loading script, or documentation of default paths is present in the provided artifacts; therefore the required environment configuration management has not been delivered.
- **T010** — The required artifact `tests/contract/test_data_download.py` does not exist in the repository, so the contract test for data download validity is missing. The task cannot be considered completed until this file is added with appropriate test code.
