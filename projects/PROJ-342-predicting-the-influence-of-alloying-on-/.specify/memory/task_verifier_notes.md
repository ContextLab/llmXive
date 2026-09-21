# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T088** — The `code/verify_report.py` script is present but its implementation is truncated (no visible exit‑code handling for detected violations) and the required `artifacts/reports/final_report.md` file does not exist, so the script cannot be run against a report containing “causes” to verify the failure behavior. The missing report file and incomplete script logic must be added for the task to be satisfied.
- **T089** — The required `.github/workflows/ci.yml` file does not exist in the repository, so the CI workflow integration cannot be verified or executed. The task’s core artifact is missing.
