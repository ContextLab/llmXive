# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The required `data/raw/checksum.txt` file does not exist, and the provided `loader.py` snippet is truncated so it’s unclear whether it writes the checksum in the exact “sha256: <hex_string>” plain‑text format or triggers the Verified Accuracy Gate on failure. The missing checksum file alone means the task’s output requirement is not met.
- **T007b** — The required `data/raw/checksum.txt` does not exist, and none of the expected result files (`results/verified_accuracy_gate.log`, `.failed`, `.done`) are present, nor is any implementation code shown that performs the checksum verification and gate logic. The task’s core functionality is therefore missing.
- **T008** — The provided `src/data/filter.py` stops after filtering and does not write the subset to `data/processed/protocol_mismatch_subset.json`, does not generate the `results/failure_mode_audit.csv` when the count is < 10 or the dominant mode differs, and does not compute or record the SHA‑256 checksum. Moreover, those output files are absent from the repository. The task’s required artifacts are therefore missing.
- **T009a** — declared artifact(s) missing/empty/invalid: assets/templates/verified_template_url.txt
- **T009b** — declared artifact(s) missing/empty/invalid: assets/templates/verified_template_url.txt, assets/templates/TEMPLATE-001-v1.0.md
