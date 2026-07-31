# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No evidence of the `data/raw/` and `data/processed/` directories or their required `.gitkeep` placeholder files is present; without these artifacts the task requirement is not satisfied.
- **T009** — No pytest configuration files (e.g., pytest.ini, setup.cfg, or pyproject.toml) or test suite files that enable `pytest-cov` are present in the provided evidence, so the requirement to configure pytest with coverage in the `tests/` directory is not satisfied. The implementer must add the appropriate configuration and ensure it is non‑empty.
- **T014a** — The `filter_text_quality` function uses a regex/length heuristic instead of the `langdetect` library with a high‑confidence threshold, and the required output file `data/processed/preprocessed_text.csv` is not present in the repository. Both the implementation and the expected artifact are missing.
- **T015** — The required input file `data/processed/preprocessed_text.csv` does not exist, so the service cannot read the pre‑processed texts as the task demands. Additionally, the provided `anxiety_scoring.py` is truncated and does not clearly show that it loads the exact model `'cardiffnlp/twitter-roberta-base-emotion'` with default float32 precision (it relies on `MODEL_NAME` from config, whose value is unknown). Both issues prevent the task from being genuinely fulfilled.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/scoring_results.csv
- **T018a** — declared artifact(s) missing/empty/invalid: data/processed/coverage_report.json
- **T021** — The provided `proxy_extractor.py` exists but the visible code contains only helper functions and no logic that actually reads `data/raw/social_media.csv`; the file is also truncated, so we cannot confirm it does so. Moreover, the required `data/raw/social_media.csv` file is missing from the repository, making it impossible for the module to read the intended input. The implementation must include code that loads the CSV and the CSV file itself must be present.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/proxy_results.csv
- **T032** — declared artifact(s) missing/empty/invalid: data/processed/final_analysis.csv
- **T036** — declared artifact(s) missing/empty/invalid: data/processed/correlation_plot.png
