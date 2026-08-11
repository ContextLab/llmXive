# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008a** — No file `specs/amendment-001-fluid-intelligence-n10.md` or its contents were presented. Consequently, the required statements about FR‑001, SC‑001, SC‑005, FR‑005, and SC‑004 amendments are not verifiable, and the verification step (writing to a temporary file and checking the content) is absent. The implementer must supply the actual markdown file with the explicit amendment text.
- **T008b** — No `specs/amendment-001-fluid-intelligence-n10.md` file or its contents were presented; the implementer did not supply the required amendment document or any proof that it was written to the specified path. The task therefore remains unfinished.
- **T008c** — No content from `specs/amendment-001-fluid-intelligence-n10.md` was provided, so we cannot verify that the required strings (FR-001, FR-005, SC-001, SC-004) are present. The implementer must supply the actual file or its relevant excerpts showing those identifiers.
- **T009** — The `ResourceMonitor` class lacks the expected attributes (`processed_dir`, `snapshots`) and does not actually write the JSON file in `finalize()`. The unit test references these missing attributes and expects a file that does not exist. Consequently, the implementation and its verification do not meet the task requirements.
- **T009b** — declared artifact(s) missing/empty/invalid: data/processed/resource_profile.json
