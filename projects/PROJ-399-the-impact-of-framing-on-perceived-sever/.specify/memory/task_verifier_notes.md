# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/raw/`, `data/processed/`, `results/plots/`, and `.github/workflows/` are reported as MISSING, so the project structure does not match the specification despite the presence of `docs/project_structure.md`.
- **T002** — The artifacts `code/DESCRIPTION` and `code/NAMESPACE` are missing entirely. Additionally, the `code/renv.lock` file is missing the required `testthat>=3.1.0` dependency.
- **T003** — No evidence of linting or formatting configuration files (e.g., `.lintr`) or related setup scripts was provided in the artifacts.
- **T006** — No evidence of environment configuration management was provided. There are no `.Renviron`, `renv.lock`, or `renv/` directory artifacts present in the project root to verify the setup.
- **T011** — The file `tests/test_statistics.R` contains tests for power calculation logic (related to User Story 3), but it completely lacks the integration tests for the mixed-effects model output format required by T011 and User Story 1. There is no evidence of tests verifying the "harm" framing coefficient, p-values, or Cohen's d.
