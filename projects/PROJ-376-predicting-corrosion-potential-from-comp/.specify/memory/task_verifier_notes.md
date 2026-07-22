# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The claim provides only a textual description of the required folder hierarchy, but no actual artifact (e.g., a directory listing, screenshot, or repository view) demonstrating that the `code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `state/`, `contracts/`, `config/`, `code/data/`, `code/models/`, `code/utils/`, and `code/tests/` directories have been created. Without concrete evidence of these directories existing, the task requirement is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — No code files or class definitions for `AlloyRecord`, `EnvironmentRecord`, or `CorrosionMeasurement` were provided; the artifact section contains no concrete implementation, so the required data model classes are missing.
- **T008** — No configuration files, scripts, or documentation for managing random seeds and file paths were provided; the claim lacks any tangible artifact demonstrating that environment configuration management has been set up. The required setup is missing.
- **T014** — The provided `code/data/preprocess.py` is truncated and does not show any logic that counts records, checks for `< 500`, writes the count to both `data/logs/pipeline.log` and `data/logs/diagnostics/count_report.txt`, or raises `DataInsufficientError`. Moreover, the two required log files are absent from the repository. Consequently, the task’s requirements are not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T017** — declared artifact(s) missing/empty/invalid: data/logs/split_validation.json
- **T021** — declared artifact(s) missing/empty/invalid: code/models/evaluate.py
- **T022** — The submission contains only the task description and specification excerpt; there is no code, data, results, or report demonstrating a null baseline (mean prediction) comparison, the R² > 0.0 classification, or a permutation‑test p‑value calculation. Consequently, the required artifact proving the “learnable” classification logic is missing.
