# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — No code files, scripts, or documentation for MD5/SHA256 checksum utility functions were presented, nor any `artifacts/checksums.txt` or related test showing the functions enforce the protocol. The required artifact is missing, so the task is not satisfied.
- **T007** — No seed‑management module or script is present in the provided evidence; there is no importable utility, documentation, or example showing how a random seed is set and propagated across analysis scripts. The required artifact is missing, so the task is not satisfied.
- **T008** — declared artifact(s) missing/empty/invalid: preprocess.yaml
- **T012** — The repository contains the `code/preprocess_microbiome.py` script, but the required output file `data/processed/microbiome_features.csv` is missing, so the pipeline’s data‑preparation result does not exist. The task is therefore not fully satisfied.
- **T013** — The repository contains `code/preprocess_eeg.py`, but the file is truncated and does not show a full implementation of downloading, filtering, ICA, epoching, alpha‑power computation, or subject‑level filtering. Moreover, the required output `data/processed/eeg_features.csv` is absent. Without a generated CSV and a complete script, the task requirements are not met.
- **T019** — The required artifact `tests/unit/test_statistics.py` does not exist in the repository, so no unit test for the FDR correction (Benjamini‑Hochberg logic) is present. The task therefore remains unfinished.
- **T023** — No `artifacts/analysis_results.json` file containing VIF values (or group‑separation statistics for Path B) is present, and no evidence of the required calculations is provided. The implementer has not supplied the mandated output, so the task remains unfinished.
