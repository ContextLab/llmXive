# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/organophosphates_filtered.csv, data/processed/sample_size_status.json, data/raw/tox21_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/organophosphates_filtered.csv, data/processed/sample_size_status.json, data/raw/tox21_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/split.py (rc=1); python code/train.py (rc=1); python -m pytest tests/ (rc=1)

## Failing / missing run-book commands

- python code/split.py -> rc=1
nts - INFO - Processing batch 1: 131 compounds
2026-10-22 09:37:04 - fingerprints - INFO - Successfully generated 131 fingerprints
2026-10-22 09:37:04 - fingerprints - INFO - Saved Morgan fingerprints to data/processed/fingerprints_morgan.pkl
2026-10-22 09:37:04 - fingerprints - INFO - Saved MACCS fingerprints to data/processed/fingerprints_maccs.pkl
2026-10-22 09:37:04 - fingerprints - INFO - Fingerprint generation complete:
2026-10-22 09:37:04 - fingerprints - INFO -   Morgan: 131 successful, 0 failed
2026-10-22 09:37:04 - fingerprints - INFO -   MACCS: 131 successful, 0 failed
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 418, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 341, in main
    raise FileNotFoundError(f"Fingerprint file still missing after generation: {fingerprint_file}")
FileNotFoundError: Fingerprint file still missing after generation: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/fingerprints.pkl

- python code/train.py -> rc=1

2026-10-22 09:37:05 - root - INFO - Starting K-Fold Cross-Validation Training (T019)
2026-10-22 09:37:05 - root - ERROR - Split indices file not found. Cannot proceed with training.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 188, in main
    raise FileNotFoundError(f"Split file not found: {split_file}")
FileNotFoundError: Split file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/split_indices.json

- python -m pytest tests/ -> rc=1
lter_validation.py::test_write_sample_size_status_ok
FAILED tests/unit/test_filter_validation.py::test_write_sample_size_status_skip
FAILED tests/unit/test_filter_validation.py::test_write_filter_log_warning - ...
FAILED tests/unit/test_filter_validation.py::test_write_filter_log_ok - TypeE...
FAILED tests/unit/test_fingerprints.py::TestMACCSFingerprint::test_maccs_fingerprint_generation
FAILED tests/unit/test_report_generator.py::test_generate_markdown_table - Ty...
FAILED tests/unit/test_report_generator.py::test_generate_markdown_table_empty
FAILED tests/unit/test_report_generator.py::test_load_metrics_from_disk - Typ...
FAILED tests/unit/test_report_generator.py::test_load_statistical_results - T...
FAILED tests/unit/test_report_generator.py::test_load_sc003_results - TypeErr...
FAILED tests/unit/test_setup_dirs.py::test_directory_creation - AssertionErro...
FAILED tests/unit/test_split.py::test_greedy_split_tanimoto_threshold - Boost...
FAILED tests/unit/test_stats.py::test_bootstrap_confidence_interval - TypeErr...
ERROR tests/unit/test_report_generator.py::test_generate_final_report - FileE...
============== 24 failed, 15 passed, 2 warnings, 1 error in 1.65s ==============


