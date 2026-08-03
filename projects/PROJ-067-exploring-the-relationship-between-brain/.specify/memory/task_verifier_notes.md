# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The `filter_subjects.py` file is present but the shown code is truncated and does not demonstrate sorting, selection, writing `data/raw/valid_subjects.json`, or raising a `FatalError` with the exact required message. Moreover, the required output file `data/raw/valid_subjects.json` is missing. The task’s core requirement—producing a JSON file with exactly 50 valid subjects or raising the specified error—is not satisfied.
- **T016** — The repository contains a `code/data/download.py` file, but it is incomplete (truncated) and cannot be verified as a working implementation. Moreover, the required `data/raw/valid_subjects.json` file does not exist, so the script has no subject list to operate on. Both required artifacts are missing or non‑functional.
- **T018** — No evidence of a modified `preprocess.py` that imports and uses `memory_monitor.py`, nor any code showing an RSS‑monitoring check that aborts when usage exceeds 7 GB, was provided. The required integration artifact is missing.
- **T019** — No `preprocess.py` file or code changes were provided showing a Framewise Displacement calculation or the logic to drop subjects with FD > 0.5 mm, so the required artifact is missing. The implementer must add the FD computation and exclusion code to the preprocessing script.
- **T020** — No code, configuration, or log files were provided showing that logging for excluded subjects (due to missing metadata or high motion) and a total processing count have been added. The artifact required to demonstrate the new logging behavior is missing.
- **T021** — No artifact (script, log, or size report) was provided to demonstrate that intermediate files are cleaned up or compressed and that the total directory size stays ≤ 7 GB as required by US1 Acceptance Scenario 1. The implementer must supply the preprocessing code and evidence (e.g., directory size check, logs) showing the size constraint is met.
- **T031** — declared artifact(s) missing/empty/invalid: data/metrics/subject_metrics.csv
- **T042** — declared artifact(s) missing/empty/invalid: results/stats.json
- **T049** — declared artifact(s) missing/empty/invalid: results/runtime_log.json
- **T050** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
