# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018a** — No `contracts/api_participant.md` file or its contents were provided; therefore the required API contract (endpoints, request/response schemas, session management details) is missing. The implementer must create the markdown file with the full specification.
- **T018b** — declared artifact(s) missing/empty/invalid: src/ParticipantForm.jsx
- **T018c** — The required file `backend/src/api/participant.py` (or an equivalent implementation) is missing from the repository, so no code handling submissions, session state, or Latin‑square assignment is present. The task’s core artifact is absent, making the implementation incomplete.
- **T012a** — The latency calibrator script exists, but the required startup files (`backend/src/main.py` or `frontend/src/App.jsx`) are missing, and there is no evidence that the calibrator is imported or executed at application launch. Integration into the startup flow has not been demonstrated.
- **T016** — The required output file `data/interaction_logs/anonymized_logs.csv` does not exist, and the provided `code/utils/anonymize_logs.py` is incomplete (truncated) with no evident entry‑point that reads raw logs and writes the anonymized CSV, so the task’s core requirement is unmet.
- **T019** — No evidence of a `data/consent/` directory, a `.gitignore` entry excluding it, or any script/command that sets file permissions to `chmod 600` is provided. The implementer’s claim cannot be verified without these artifacts.
- **T027** — The required artifact `github/workflows/test_reproducibility.yml` does not exist, so no integration test for CI resource constraints is present. The task’s core deliverable is missing.
- **T030a** — The `baseline_results.json` file, which the task explicitly requires to be generated and committed, is missing. Moreover, the provided `generate_baseline_results.py` is truncated and only attempts to load existing CSV/JSON files rather than executing the analysis script and writing the required JSON output. The core functionality and output artifact are therefore absent.
- **T030** — declared artifact(s) missing/empty/invalid: github/workflows/test_reproducibility.yml
- **T029** — No README.md file or its contents were provided; the claim lacks any artifact showing documentation for rerunning the analysis on GitHub Actions under the specified free‑tier constraints. Consequently the required deliverable is missing.
- **T031** — declared artifact(s) missing/empty/invalid: data/reproducibility_package_v1.0.tar.gz, data/analysis_results/results.csv, data/interaction_logs/anonymized_logs.csv
- **T032** — The required `state/projects/PROJ-140.../artifact_hashes.yaml` file is missing, so no hashes have been provided. The task’s core deliverable is absent.
- **T033** — No README.md file or its contents were presented, so we cannot verify that installation steps and dependencies were added. The required artifact is missing from the evidence.
