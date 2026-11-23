# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — declared artifact(s) missing/empty/invalid: code/tests/integration/test_training.py
- **T013** — The `code/data/download_zinc.py` script is present but its implementation is truncated (the `load_dataset` call is incomplete) and it never writes any checksums to `data/checksums.json`. Moreover, the required `data/checksums.json` file does not exist. The task’s core requirements—downloading via `datasets.load_dataset('zinc15', split='train')`, verifying the canonical source, and saving checksums—are therefore not fulfilled.
- **T013b** — No script or code file was provided that checks a ZINC15 dataset ID against the canonical ZINC15 source URL and logs the outcome, so the required artifact is missing. The implementer’s claim cannot be verified without the actual script.
