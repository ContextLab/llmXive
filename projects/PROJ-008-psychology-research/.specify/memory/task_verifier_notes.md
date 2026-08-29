# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-008-psychology-research/` directory or any of its required sub‑folders/files is provided. The implementer did not supply the project structure, so the task’s core deliverable is missing.
- **T003** — The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) nor any documentation showing that `ruff` and `black` have been set up and integrated into the project. Consequently, the required artifact for task T003 is missing.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_studies.csv, data/raw/excluded_studies.log
- **T029** — No code, configuration, or documentation was provided that shows the required conditional logic (suppressing subgroup/meta‑regression when total N < 10 and falling back to a descriptive synthesis). Without any artifact to inspect, we cannot confirm the feature was implemented. The missing deliverable is the implementation (e.g., function, script, or module) and evidence (tests or logs) demonstrating the N‑threshold behavior.
- **T033** — The required artifact `tests/integration/test_bias.py` is missing from the repository, so no integration test for Egger's test exists to satisfy the task. The implementer must add a non‑empty test file at that path that actually runs the publication bias assessment.
- **T037** — No code, script, or report artifact was provided that demonstrates the required conditional logic to suppress the funnel plot and Egger’s test when the total sample size N < 10, nor the addition of a warning to the final report. The implementer’s claim cannot be verified without such concrete evidence.
