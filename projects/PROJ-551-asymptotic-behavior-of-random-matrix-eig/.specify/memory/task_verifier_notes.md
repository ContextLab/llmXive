# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — No `.npy` matrix file under `data/raw/` nor a `state/checksums_raw.json` file was presented. Consequently the required atomic generation and checksum recording cannot be confirmed. The implementer must provide the actual NumPy file and the JSON checksum entry.
- **T019b** — declared artifact(s) missing/empty/invalid: data/processed/single_run_results.json
- **T040a** — No `.npy` matrix files under `data/raw/sweep/` nor a `state/checksums_sweep.json` file were presented. Without these files and their SHA‑256 entries, the required grid sweep and atomic checksum recording have not been demonstrated. The implementer must provide the generated matrix files and the corresponding checksum JSON.
- **T021b** — declared artifact(s) missing/empty/invalid: data/processed/mc_results.csv, data/processed/threshold_identification.json
- **T037** — The claim references new unit test files in `tests/unit/`, but no such files or code snippets are provided in the evidence. Without the actual test files (or their contents) we cannot verify that edge‑case tests for N=100, θ=1.0, rank=0 exist or are correctly implemented. The required artifact is missing.
