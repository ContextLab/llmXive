# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — declared artifact(s) missing/empty/invalid: data/neural/processed/roi_timecourses.csv
- **T014** — No code, script, or documentation implementing chunked loading/subsampling for large fMRI datasets is present; the only evidence is the task description itself, with no concrete artifact to verify the feature. The required implementation and any associated tests or usage examples are missing.
- **T015** — The required output file `data/text/rocstories_sample.jsonl` does not exist, so the ROCStories corpus has not been downloaded and sampled as specified. The implementer must create this JSONL file with a representative subset of stories in the indicated path.
- **T016** — No validation script or code was provided that checks for corrupted or incomplete data and aborts with specific error messages. The required artifact (e.g., a Python/ Bash validation step integrated into the data pipeline) is missing, so the task’s requirement is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/neural/processed/event_averages.csv
- **T018** — No evidence of `utils/checksums.py` being executed or of a state file being updated is provided; the required artifact (updated state file with checksum entries) is missing, so the task’s requirement is not demonstrably satisfied.
- **T025** — No training‑loop script, configuration, or logs are present; there is no code implementing a retry mechanism across three random seeds for the sparse autoencoder (SAE), nor any evidence (e.g., saved model checkpoints, convergence plots) that such a loop was executed. The required artifact is missing.
