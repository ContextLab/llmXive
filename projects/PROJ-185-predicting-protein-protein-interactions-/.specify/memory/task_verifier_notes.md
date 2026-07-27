# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required repository skeleton directories (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`) is present; the provided material only contains a feature specification and no filesystem artifacts. The task therefore remains unfinished.
- **T001d** — No CI configuration, script, or workflow file was presented that checks for the presence of required skeleton directories and causes the CI job to fail if any are missing. The implementer supplied no artifact matching the task’s requirement, so the claim of completion is unsupported.
- **T003** — No `renv.lock` file, R initialization script, or any evidence of the listed Bioconductor packages being installed is present. The required artifact (the environment lockfile and installation steps) is missing, so the task is not satisfied.
- **T003c** — No `renv.lock` file, nor any unit‑test code or test results were provided; without these artifacts we cannot verify that a test checks the lockfile’s existence and that it records package versions. The required test and lockfile are missing.
- **T003d** — No unit‑test file or script is present in the provided evidence; there is no code that runs `Rscript -e "renv::status()"` and checks for a non‑zero exit status. The required test artifact is missing, so the task is not satisfied.
- **T004c** — The repository contains a `pyproject.toml` file, but the required `.ruff.toml` (or `ruff.toml`) linting configuration file is missing, and no unit test is provided to confirm that the linting configuration is runnable. Both the presence of the `.ruff.toml` file and a test exercising the linting setup are required to satisfy task T004c.
- **T005** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- **T005c** — No CI workflow file (e.g., `.github/workflows/*.yml`) was presented, and there is no evidence that any such file contains a `validate` job. The required artifact is missing, so the task is not satisfied.
- **T005d** — No CI script, configuration, or test files that validate the workflow file structure were presented. The claim provides only a high‑level feature specification unrelated to a CI validation step, and there is no artifact (e.g., a GitHub Actions workflow, a validation script, or test results) to confirm that such a CI step exists or works. The required CI validation artifact is missing.
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T006c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: species.yaml, parameters.yaml
- **T009c** — Both required files `species.yaml` and `parameters.yaml` are reported as missing, so the unit test that verifies their presence cannot pass. The artifact needed to satisfy the task does not exist.
- **T009d** — The provided information contains only the high‑level feature specification for PPI prediction; there is no CI configuration, benchmark script, or runtime log showing a step that enforces the overall pipeline to finish within 6 hours. Consequently, the required artifact (a CI step that checks and limits total runtime using the benchmark script) is missing.
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010c** — The claim provides no unit‑test code, test output, or proof that any YAML/JSON schema files were parsed and validated; no files or logs are presented to demonstrate syntactic checking. Consequently, the required artifact (a test confirming all schema files are valid) is missing.
- **T010d** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010e** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010f** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010g** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011c** — The claim provides only the high‑level feature specification and user stories; there is no evidence of a verification script, nor any CI configuration or logs showing that the script is executed after each `make` target as required by FR‑017. The necessary artifact (e.g., a script, GitHub Actions step, or Makefile modification invoking the verification step) is missing.
- **T012** — declared artifact(s) missing/empty/invalid: src/cli/validator.py
- **T012c** — The required artifact `tests/unit/test_cli_threshold.py` does not exist in the repository, so the unit test for the CLI validator cannot be verified. The task remains unfinished until the file is added with appropriate test code.
- **T012d** — The provided evidence only describes a PPI prediction pipeline and its evaluation; there is no code, configuration, test, or documentation showing that a `--seed` argument is now passed to the correlation, baseline, negative‑sampling, or sensitivity modules. Consequently, the requirement of global seed propagation is not demonstrated. The implementer must supply the updated scripts/CLI definitions and/or tests confirming the seed is forwarded to all stochastic components.
- **T098** — No code changes, configuration, or example `pipeline.log` showing the added command‑line, version, and seed information were provided; thus the required logger extension cannot be verified. The implementer must supply the modified logger implementation and a sample log entry demonstrating the new fields.
