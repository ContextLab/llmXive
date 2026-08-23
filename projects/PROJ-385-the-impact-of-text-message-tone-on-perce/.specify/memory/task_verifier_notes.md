# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T090** — The required artifact `data/processed/cue_intensity_weights.json` does not exist, so the cue‑intensity weighting schemes have not been defined or stored as specified. The task therefore remains unfinished.
- **T091** — declared artifact(s) missing/empty/invalid: data/processed/power_analysis_results.json
- **T092** — The script `code/04_fit_lmm.py` correctly references `data/processed/anonymised_ratings.csv`, but the required file `data/processed/anonymised_ratings.csv` is missing, so the guard cannot be exercised and the CI step would fail. The missing CSV must be provided for the verification to be complete.
- **T093** — declared artifact(s) missing/empty/invalid: data/manifest.json
- **T050** — The `data/checksums.json` file exists but contains an empty object (`{}`) and does not include the required SHA‑256 checksum entry for `data/raw/stimuli.csv`. The checksum needs to be computed and recorded in the JSON file.
- **T010a** — The contract test file and `data/raw/stimuli.csv` exist, but the required `stimulus.schema.yaml` is missing, so the test cannot load the schema and will fail when run with pytest. The missing schema file must be added (and correctly referenced) for the task to be satisfied.
- **T054** — declared artifact(s) missing/empty/invalid: data/raw/real_ratings.csv, data/checksums.json
- **T052** — declared artifact(s) missing/empty/invalid: data/processed/anonymised_ratings.csv, data/checksums.json
- **T086** — The required file `data/processed/anonymised_ratings.csv` is missing, so there is no data to validate the `participant_id` column against the Participant schema. The task cannot be considered completed until this file exists and contains a non‑null `participant_id` column as specified.
- **T016** — The required output file `data/processed/cleaned_ratings.csv` does not exist, and the provided `code/03_clean_data.py` is truncated before completing the straight‑lining detection (and shows no missing‑data handling or logging of exclusions). Consequently the task’s deliverables are not satisfied.
