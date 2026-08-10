# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `src/services` directory or an empty `.gitkeep` file was provided; without these artifacts the claimed task cannot be verified as completed. The required directory and placeholder file must be added to the repository.
- **T001b** — No evidence of a `src/models` directory or an empty `.gitkeep` file was provided; without these artifacts the requirement cannot be confirmed as satisfied. The implementer must add the directory and the placeholder file to the repository.
- **T001c** — No artifact showing a `src/utils` directory or an empty `.gitkeep` file was provided; without visible evidence the requirement cannot be confirmed as satisfied.
- **T001d** — No evidence of a `src/data-models` directory or a `.gitkeep` file was provided; without seeing those artifacts, we cannot confirm the required directory and empty placeholder file exist. The implementer must add the directory and an empty `.gitkeep` file inside it.
- **T001e** — No artifact showing a `tests/unit` directory or an empty `.gitkeep` file was provided; without such evidence the requirement cannot be confirmed as fulfilled.
- **T001f** — No evidence of a `tests/contract` directory or an empty `.gitkeep` file was provided; the required artifact is missing.
- **T001g** — No `data/raw` directory or `.gitkeep` file is present in the provided evidence; the required artifact is missing, so the task is not satisfied.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — declared artifact(s) missing/empty/invalid: src/services/download.py
- **T013** — The `src/services/filter.py` file is present and correctly raises `ValueError` for malformed JSON, but `src/services/download.py` is missing entirely, so the required update to raise `FileNotFoundError` cannot be verified. The task is therefore not fully completed.
- **T017** — declared artifact(s) missing/empty/invalid: src/models/vlm.py
- **T018** — declared artifact(s) missing/empty/invalid: src/services/scoring.py
- **T019** — declared artifact(s) missing/empty/invalid: src/services/scoring.py
- **T020** — declared artifact(s) missing/empty/invalid: src/services/scoring.py
- **T024b** — The repository lacks the required `outputs/circular_validation_risk_report.json` file, and the provided `src/services/analysis.py` does not contain any implementation that writes this JSON atomically using a temporary file and `os.rename()`. Consequently, the task’s core requirement is not satisfied.
- **T024** — The provided `src/services/analysis.py` is truncated and shows no implementation of the required Pearson‑correlation independence check, atomic JSON write, or raising of `CircularValidationRiskError`. Moreover, the required output file `outputs/circular_validation_risk_report.json` does not exist. The task’s core behavior is therefore not present.
