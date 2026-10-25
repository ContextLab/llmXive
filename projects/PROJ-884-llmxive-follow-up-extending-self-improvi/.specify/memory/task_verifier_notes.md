# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The generator and verifier scripts exist and can produce JSONL records that validate against `contracts/dataset.schema.yaml`, and the verifier returns a `(bool, error_code)` tuple. However, the verifier’s timing log is never created because `data/processed/verifier_timing.log` (and its parent directory) do not exist, and the code does not create them before writing. Consequently the requirement “records a timing entry in `data/processed/verifier_timing.log`” is not satisfied. Adding code to ensure the `data/processed` directory is created (e.g., `Path(log_path).parent.mkdir(parents=True, exist
- **T003** — Requested task execution failed; rerun successfully: code/bes/main.py exit=1
