# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — `requirements.txt` exists with all ten required pinned dependencies (plus an extra `arxiv` entry, which is harmless), but the required `requirements-optional.txt` containing `easyocr==1.7.*`, `opencv-python==4.8.*`, and `pdf2image==1.16.*` is missing entirely. The implementer must create that optional dependencies file to satisfy the task.
- **T002b** — The `requirements.txt` exists and contains a plausible pinned dependency list, but the task's action is to run `pip check` (or equivalent) and its verification criterion is "no dependency conflicts reported" — and no execution evidence of such a check (command output, log, or report) was provided. The implementer's claim that dependencies are resolvable is unverified; the next step should capture and attach actual `pip check` / `pip install --dry-run` output against this file.
- **T003a** — The evidence collector shows no artifacts on disk for this task — there is no `.flake8` file (or any resolved path) present in the project, so the required configuration file with `max-line-length = 88` does not exist. The implementer must create `.flake8` at the project root containing that setting.
- **T004** — The evidence collector provided no artifacts confirming a `.git` directory, a `.gitignore` file, or any `git log` output showing an initial commit in `projects/PROJ-349-predicting-the-impact-of-ball-milling-on`. The task's verification criteria (`.git` exists and `git log` shows an initial commit) are entirely unmet by the supplied evidence — the implementer must actually run `git init`, add a `.gitignore`, and create the initial commit, and the evidence must show it.
- **T020** — declared artifact(s) missing/empty/invalid: src/ingest/streaming_utils.py
- **T014b** — declared artifact(s) missing/empty/invalid: src/ingest/flagger.py, data/flagged_psd.log
- **T067** — declared artifact(s) missing/empty/invalid: src/preprocess/derive_duration.py
- **T017a** — declared artifact(s) missing/empty/invalid: data/processed/ball_milling_dataset.parquet
- **T062** — declared artifact(s) missing/empty/invalid: src/model/bin_calculator.py
- **T063** — declared artifact(s) missing/empty/invalid: src/model/bin_calculator.py
- **T021#1** — declared artifact(s) missing/empty/invalid: src/model/train_gpr.py, src/model/train_rf.py
- **T029a** — declared artifact(s) missing/empty/invalid: src/model/train_gpr.py
- **T029b** — declared artifact(s) missing/empty/invalid: src/model/train_rf.py
- **T068** — declared artifact(s) missing/empty/invalid: src/model/resource_monitor.py
- **T071** — declared artifact(s) missing/empty/invalid: src/cli/train.py
- **T072** — declared artifact(s) missing/empty/invalid: src/cli/train.py
- **T025** — declared artifact(s) missing/empty/invalid: src/model/baseline_lr.py
- **T026** — declared artifact(s) missing/empty/invalid: src/evaluate/metrics.py, results/metrics.csv
- **T026b** — declared artifact(s) missing/empty/invalid: src/evaluate/nested_cv_report.py
- **T030** — declared artifact(s) missing/empty/invalid: results/power_analysis_result.txt
- **T070** — declared artifact(s) missing/empty/invalid: results/power_analysis_result.txt, results/t_test_power.txt
- **T033** — declared artifact(s) missing/empty/invalid: src/interpret/partial_dependence.py
- **T034** — declared artifact(s) missing/empty/invalid: src/interpret/feature_importance.py, results/feature_importance.json
- **T037** — declared artifact(s) missing/empty/invalid: src/utils/generate_report.py, results/final_report.md
- **T038** — declared artifact(s) missing/empty/invalid: .github/workflows/ci.yml
- **T056** — declared artifact(s) missing/empty/invalid: src/cli/train.py, data/processed/small_sample.parquet
