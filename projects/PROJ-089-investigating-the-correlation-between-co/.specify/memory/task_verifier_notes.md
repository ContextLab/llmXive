# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — No spec.md or plan.md files (or excerpts thereof) were presented, and no written identification of the stated contradiction was supplied. The required evidence that the implementer read the artifacts and pinpointed the mismatch is missing.
- **T007b** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T007c** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T007d** — No `main.py` file or any code was presented that calls `run_extraction`, `run_analysis`, and `run_reporting` sequentially, nor evidence that it runs the full pipeline on mock data. The required artifact is missing.
- **T010** — declared artifact(s) missing/empty/invalid: data/raw/repos_metadata.csv
- **T010a** — declared artifact(s) missing/empty/invalid: data/raw/repos_metadata.csv
- **T011** — No evidence of a `data_extraction.py` script or a populated `data/raw/git_history/` directory is provided; without these artifacts we cannot confirm that repositories were cloned and per‑file commit/line‑change data were extracted as required. The implementer must supply the script and the resulting raw git‑history files.
- **T013b** — The required `utils.py` implementation is absent, the `citations.csv` file (needed for fallback validation) is missing, and the provided `tool_validation_log.csv` lacks star count data and any DEVIATION entry, indicating the validation logic was not fully realized.
- **T014** — No evidence of a `static_analysis.py` script or the required `data/raw/static_analysis/{repo_id}/semgrep_results.json` files is present; without these artifacts the static analysis step and debt score calculations cannot be confirmed. The implementer must provide the script and the generated JSON results for each repository.
- **T015a** — declared artifact(s) missing/empty/invalid: data/processed/filtered_metrics.csv
