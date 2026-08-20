# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The required output file `data/processed/roi_timecourses.csv` does not exist, so the combined timecourse data is missing and the task’s specification is not satisfied. The implementer must create the CSV with the specified columns.
- **T019** — The required output file `data/text/rocstories_sample.jsonl` does not exist, so the ROCStories corpus has not been downloaded and sampled as specified. The task’s core requirement is missing.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/event_averages.csv
- **T022** — No checksum output, log, or updated state file is provided as evidence that `utils/checksums.py` was executed after data processing. The required artifact (the updated state file reflecting new checksums) is missing, so the task is not demonstrably completed.
- **T029** — No code, script, or test output showing a training loop with retry logic, seed increment, sparsity measurement, or the required E003 error is present. The artifact needed to demonstrate the core training loop and its retry behavior is missing.
- **T037** — The provided `code/03_rsa_analysis.py` contains data‑loading and RSA utilities but no implementation of the required permutation test (convergence logic, timeout handling, or “borderline” flag). Moreover, the expected output file `data/results/permutation_test_results.json` is absent. Both the core functionality and the result artifact are missing.
