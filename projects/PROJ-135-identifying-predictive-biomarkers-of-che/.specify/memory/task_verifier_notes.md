# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — No schema files, checksum definitions, or any related artifacts are present in the provided evidence; the only content shown is a feature specification and user stories, which do not fulfill the “implement schema files and checksums” requirement. The required files are missing.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils.py
- **T011** — The provided `test_feasibility_gate.py` file is truncated, so we cannot see whether it actually contains the required assertions for the two scenarios. Moreover, the expected output file `data/feasibility_gate.json` is absent from the repository, and there is no evidence that the test creates and validates it. The implementer must supply the full test code with explicit checks for the halted status/reason and ensure the test generates and verifies `data/feasibility_gate.json`.
- **T023** — declared artifact(s) missing/empty/invalid: src/biomarker_discovery.py
- **T024** — No code, data files, or generated gene panel were supplied; the implementer did not provide the static gene panel, scripts, or results required by the user stories. Consequently, the task’s deliverables are missing.
- **T025** — No artifact or evidence is provided showing that task T025 has been removed or merged into T024 (e.g., updated task list, commit removing the file, or documentation of the merge). Without such proof, we cannot confirm the removal was performed.
- **T026** — No artifact or evidence is provided showing that task T026 has been removed or merged into T024 (e.g., updated task list, commit, or documentation). Without such proof, we cannot confirm the removal was performed.
- **T027** — No artifact (e.g., commit diff, pull‑request, or file deletion) was provided to demonstrate that task T027 was actually removed/merged into T024. Without concrete evidence of the removal, the claim cannot be verified.
