# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: projects/PROJ-405/
- **T001b** — The evidence shows that `projects/PROJ-405/code/` is missing and there is no `artifacts/` subdirectory present, so the required directory structure has not been fully created.
- **T001c** — declared artifact(s) missing/empty/invalid: projects/PROJ-405/specs/001-predict-plant-disease-severity/
- **T003** — The evidence provides no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or a `black` config) nor any scripts or documentation showing that ruff/flake8 and black have been set up and integrated into the project. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- **T047** — The provided `plan.md` does not contain a Step 0.4 with the required revised wording; it still references “expert‑labeled ground truth severity scores” and lacks the exact sentence “Verify non-null values for image features and weather variables. Study is observational; no ground truth exists.”. The plan must be edited to replace those phrases and add the specified text in Step 0.4.
- **T048** — The `plan.md` file does include a fallback to query the NOAA GHCN‑Daily API and to exclude records when both APIs fail, but it does **not** contain the required phrasing “NOAA GHCN‑Daily API query via `requests` library” nor the explicit statement “No local CSVs.” These exact textual updates are missing, so the task’s specification is not fully satisfied.
- **T049** — Checked `research.md` (7033 bytes) – it discusses construct validity and mentions “frame results as ‘associational’” but does **not** contain the required explicit sentence: “No ground truth validation is performed due to absence of expert labels; findings are framed as associational.” The mandated statement is missing.
- **T016a** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
- **T043b** — declared artifact(s) missing/empty/invalid: code/utils/docs.py, state/
