# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw`, `data/processed`, `data/models`) was provided; the artifact list is empty, so the task of creating those folders has not been demonstrated. The implementer must add the three directories to the repository (and ensure they are non‑empty or at least present) for the task to be considered complete.
- **T001b** — declared artifact(s) missing/empty/invalid: data/.setup_verification.log
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black/Ruff settings, `.flake8`, or similar) are present in the provided evidence, so the requirement to configure ruff/flake8 and Black has not been demonstrated.
- **T004** — No GitHub Actions workflow file (e.g., `.github/workflows/ci.yml`) was presented, nor any description of its contents showing installation of R‑base and Python dependencies. Without the actual CI configuration artifact, the requirement cannot be confirmed as satisfied.
- **T004b** — No CI configuration, script, or command file was provided that shows system‑level installation of the R packages `lme4` and `ordinal`. Without such an artifact, we cannot confirm that the R environment setup task was actually implemented. The required evidence (e.g., a `.github/workflows/*.yml` snippet or shell script invoking `Rscript -e "install.packages(...)"`) is missing.
