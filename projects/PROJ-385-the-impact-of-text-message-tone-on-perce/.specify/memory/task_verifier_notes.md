# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T090** — The required artifact `data/processed/cue_intensity_weights.json` does not exist, so the cue‑intensity weighting schemes have not been defined or stored as specified. The task therefore remains unfinished.
- **T091** — declared artifact(s) missing/empty/invalid: data/processed/power_analysis_results.json
- **T092** — The required script `code/04_fit_lmm.py` does not exist, and the processed data file `data/processed/anonymised_ratings.csv` is also missing, so the guard cannot be verified. Both artifacts must be present and contain the appropriate path checks.
- **T093** — declared artifact(s) missing/empty/invalid: data/manifest.json
- **T013** — The required output file `data/raw/stimuli.csv` does not exist, and the provided `code/01_generate_stimuli.py` is truncated (e.g., `categorize_length` is incomplete) with no evidence that it writes the specified columns or that the `--verify` mode produces the required log message. The task’s core deliverables are therefore missing.
- **T050** — The required file `data/raw/stimuli.csv` does not exist, and the JSON entry contains a placeholder hash rather than the actual SHA‑256 checksum of the file. Both the artifact and a correct checksum are missing.
- **T010a** — The provided `tests/contract/test_stimulus_schema.py` exists but is truncated (e.g., the `test_data_types` function ends abruptly) and the required data files `data/raw/stimuli.csv` and the schema file `stimulus.schema.yaml` are absent, so the contract test cannot run or pass.
- **T041** — The required artifact `data/raw/real_ratings.csv` does not exist on disk, so the verification script cannot confirm its presence or trigger an error as specified. The task’s core requirement—ensuring the file exists before downstream analysis—is unmet.
- **T051** — declared artifact(s) missing/empty/invalid: data/raw/real_ratings.csv, data/processed/anonymised_ratings.csv
