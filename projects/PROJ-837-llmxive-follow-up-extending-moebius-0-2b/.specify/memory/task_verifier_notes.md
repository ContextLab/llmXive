# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — declared artifact(s) missing/empty/invalid: data/annotations/human_scores.csv, data/annotations/krippendorff_raw.json, data/results/validation_log.txt
- **T016** — The provided `annotator.py` only logs errors and returns booleans; it does not raise exceptions when sample size is below 50 or when label independence fails. Moreover, the required `data/results/validation_log.txt` file is absent. Both the error‑raising behavior and the logging artifact are missing.
- **T035** — The provided `code/eval/stats.py` stops after loading metrics and scores and never computes Pearson’s r, applies the required gating logic, or writes `proxy_validation.json`. Moreover, the expected output file `data/results/proxy_validation.json` does not exist. The task’s core functionality is missing.
- **T037** — declared artifact(s) missing/empty/invalid: data/results/proxy_validation.json
- **T025** — The repository contains `code/eval/stats.py`, but the shown portion does not include any function that runs a permutation test with `scipy.stats.permutation_test` nor writes a p‑value and gate status to `data/results/permutation_test.json`. Moreover, the expected output file `data/results/permutation_test.json` is absent. The task’s core requirement is therefore unmet.
- **T033a** — declared artifact(s) missing/empty/invalid: data/results/latency_raw.csv
