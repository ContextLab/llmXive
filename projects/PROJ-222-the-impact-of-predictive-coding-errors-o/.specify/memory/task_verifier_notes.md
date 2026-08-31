# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The provided `code/download.py` is present but the visible portion stops after a partially‑implemented `fetch_openml_dataset` and does not show the required checksum‑verification against the source API, column filtering, exclusion logging, or README updates. Moreover, there are no raw dataset files in `data/raw/` and the exclusion log is empty, giving no proof that the script actually fetched and validated any datasets. The task’s full pipeline is therefore not demonstrated.
- **T016** — The repository contains a `code/preprocess.py` file, but the visible portion shows only dataset loading and basic checks; there is no implementation of a Markov‑based surprisal calculation nor any code that writes `data/processed/markov_state.json`. Moreover, the required output file `data/processed/markov_state.json` is absent from the project. The task’s core requirement is therefore unmet.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/standardized.csv
