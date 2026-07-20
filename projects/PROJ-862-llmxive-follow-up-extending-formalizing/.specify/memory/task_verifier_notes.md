# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T013** — The provided `code/data_loader.py` only contains dataset loading and validation utilities; it lacks any function that pairs questions by task type, assigns `PairID`s, or writes `data/processed/pairing_config.json`. Moreover, the required `pairing_config.json` file does not exist. Both the implementation and the expected output artifact are missing.
- **T015** — The provided `code/main.py` is incomplete (it ends abruptly inside `extract_baseline_vectors` and does not contain the full extraction‑normalize‑save loop). Moreover, the required output file `data/processed/baseline_vectors.csv` is absent. Both the implementation and the generated artifact are missing, so the task is not genuinely fulfilled.
- **T016** — No code, tests, or documentation were provided that adds validation to ensure output vectors match the model’s hidden dimension and are L2‑normalized. The claim lacks any artifact (e.g., a function, unit test, or example output) demonstrating the required checks, so the task is not satisfied.
- **T017** — No code, configuration, or log files were provided showing that progress or memory‑usage logging was added to the baseline extraction pipeline. Without any artifact demonstrating new logging statements or generated logs, the requirement cannot be verified as met.
