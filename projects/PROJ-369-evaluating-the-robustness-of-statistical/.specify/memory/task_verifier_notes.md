# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T061** — The provided `src/data/ingestion.py` contains only download‑validation code and does not implement any sampling rule (e.g., `itertools.islice` or seeded random sample) nor logging of sample size/method. Additionally, the required `data/processed/sampling_metadata.json` file is absent. Both artifacts needed to satisfy the task are missing.
- **T062** — No code, configuration, log output, or documentation was presented showing that T020 was modified to detect series shorter than 25 points, skip them, and emit a detailed warning with the dataset ID and length. Without such artifacts, the requirement cannot be verified as satisfied.
- **T063** — No code, configuration, test, or documentation artifact showing a maximum differencing limit, critical‑error logging, or pipeline halting was provided. Without such files or evidence, we cannot confirm that T021 was enhanced as required. The implementer must supply the modified source (e.g., the preprocessing module) and any associated tests or logs demonstrating the new edge‑case handling.
- **T065** — declared artifact(s) missing/empty/invalid: src/analysis/regression.py
- **T067** — declared artifact(s) missing/empty/invalid: data/results/integrity_report.json
