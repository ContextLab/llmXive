# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No repository skeleton directories (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`) are present in the provided evidence; the implementer supplied only a textual claim without any actual folder structure or files. The required artifact is missing.
- **T003** — No `renv.lock` file, R project initialization script, or any evidence of the listed Bioconductor packages being installed is provided. The required artifact (a reproducible R environment setup) is missing, so the task is not satisfied.
- **T004** — The claim provides no linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, `.style.yapf`, or similar) and no evidence that `ruff`, `black`, or `styler` have been added to the project. The artifacts listed are unrelated to the linting task, so the required configuration is missing.
- **T005** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T007** — declared artifact(s) missing/empty/invalid: src/cli/run_pipeline.py
- **T009** — declared artifact(s) missing/empty/invalid: species.yaml, parameters.yaml
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The claim provides no code, file, or snippet showing a CLI argument validator in `run_pipeline.py`, nor any test or documentation confirming that `--threshold` is enforced to be ≥ 0.75. Without the actual artifact, the requirement is not satisfied.
- **T013** — No CI configuration, script, or workflow file is provided that adds a citation‑verification step, nor any evidence (e.g., GitHub Actions YAML, test logs, or documentation) showing the Reference‑Validator Agent being invoked on markdown and code files. The required artifact is missing, so the task is not satisfied.
- **T098** — No code changes, configuration, or example `pipeline.log` showing the added command‑line, version, and seed information were provided; thus the required logger extension cannot be verified. The implementer must supply the modified logger implementation and a sample log entry demonstrating the new fields.
- **T099** — No test script, CI configuration, or code artifact was presented that runs the CLI validator with a threshold below 0.75 and checks for rejection. The required CI test file (e.g., a pytest or GitHub Actions step) is missing, so the claim is unsupported.
- **T100** — The implementer provided no CI configuration, script, or workflow file that runs a Reference‑Validator Agent, nor any evidence that the pipeline would fail on citation mismatches. Consequently, the required artifact is missing.
- **T064** — declared artifact(s) missing/empty/invalid: src/pipeline/download.py, state/artifact_hashes.yaml
- **T043** — No code changes, log files, or test output were provided to demonstrate that the downloader now checks sample counts, skips series with fewer than 30 samples, and writes a warning to `pipeline.log`. Without such artifacts, the requirement cannot be verified as satisfied.
