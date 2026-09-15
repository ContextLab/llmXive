# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002b** — The required `requirements.txt` file is missing, so no dependencies could be installed or verified in a virtual environment. Without the file, the implementer could not fulfill the installation and verification steps.
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No `.env` file, configuration‑loading code, or documentation of relative‑path handling is present in the provided artifacts. The implementer has not supplied any evidence that environment configuration management was set up, so the requirement is unmet.
- **T039** — The required artifact `data/processed/robustness_report.json` does not exist in the repository, so the robustness metrics have not been aggregated as specified. The implementer must create this JSON file containing the requested metrics.
- **T040a** — No `README.md` file or its contents were supplied; therefore we cannot confirm that installation instructions and usage examples were added. The required artifact is missing.
- **T040b** — No evidence of the `specs/001-gene-regulation/quickstart.md` file being present or containing the required project overview and data requirements was provided. The implementer must supply the updated markdown file with the specified content.
- **T041** — No code files from `code/analysis/` or `code/data/` were provided, so we cannot verify that unused imports were removed, line length limits were enforced, or docstrings were added to all public functions. The required artifacts are missing.
- **T042** — No code, script, configuration, or benchmark was provided showing that the data loading step has been modified to stream only the required columns and stay within GB‑scale RAM usage. The claim lacks any tangible artifact (e.g., a revised data‑loader implementation, memory‑usage logs, or performance test results) to verify the optimization. Consequently, the task requirement is not satisfied.
- **T043** — No pytest execution logs, result files, or any evidence that a test suite was run and all contract tests passed are present. Without such artifacts, we cannot confirm the task was actually completed.
