# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — The required output file `data/raw/study_manifest.json` is missing, and the provided `verify_studies.py` script is truncated before any code that creates/writes the manifest (the `main()` function is incomplete). Without the generated JSON file, the task’s verification criteria are not met. The next implementer must ensure the script writes a non‑empty, valid JSON manifest to the specified path.
- **T012b** — declared artifact(s) missing/empty/invalid: data/raw/study_manifest.json
