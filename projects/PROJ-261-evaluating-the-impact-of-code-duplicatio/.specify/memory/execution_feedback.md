# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 command(s) failed: python code/quickstart_validation.py validate_directory_structure (rc=1); python code/main.py (rc=1); python code/bug_detection.py # Stage 4: Bug detection (rc=1); 2 declared deliverable(s) absent: data/analysis/correlation_results.csv; data/raw/github-code-sample.csv

## Failing / missing run-book commands

- python code/quickstart_validation.py validate_directory_structure -> rc=1
    S
2026-06-29 03:41:11 - __main__ - INFO -   Documentation Validation: FAIL
2026-06-29 03:41:11 - __main__ - INFO -   Output Validation: WARN
2026-06-29 03:41:11 - __main__ - INFO -   Overall: FAIL
2026-06-29 03:41:11 - __main__ - INFO - ------------------------------------------------------------
2026-06-29 03:41:11 - __main__ - ERROR - Quickstart validation FAILED. Please review the errors above.
- python code/main.py -> rc=1
     Raw data not found, skipping data loading
2026-06-29 03:41:11,837 - INFO - Computing perplexity scores...
2026-06-29 03:41:11,837 - ERROR - Perplexity computation failed: cannot access local variable 'sample_files' where it is not associated with a value
2026-06-29 03:41:11,837 - ERROR - Pipeline execution failed: cannot access local variable 'sample_files' where it is not associated with a value
- python code/bug_detection.py # Stage 4: Bug detection -> rc=1
    172, in record_artifact_checksums
    manifest = load_manifest(manifest_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/checksum_manifest.py", line 100, in load_manifest
    if not manifest_path.exists():
           ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'exists'
- python code/correlation_analysis.py # Stage 5: Correlation analysis -> rc=1
    2026-06-29 03:58:11,167 - ERROR - Perplexity scores not found: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/processed/perplexity_scores.csv
- python code/visualization.py # Stage 6: Visualizations -> rc=1
    dom seed: 42
2026-06-29 03:58:12,808 - INFO - Figure formats: png
2026-06-29 03:58:12,808 - INFO - Figure DPI: 300
2026-06-29 03:58:12,808 - ERROR - Correlation results not found: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/analysis/correlation_results.csv
2026-06-29 03:58:12,808 - ERROR - Cannot generate visualizations without correlation data
- python code/correlation_analysis.py --threshold 0.7 & -> rc=1
    2026-06-29 03:58:12,964 - ERROR - Perplexity scores not found: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/processed/perplexity_scores.csv
- python code/correlation_analysis.py --threshold 0.8 & -> rc=1
    2026-06-29 03:58:13,077 - ERROR - Perplexity scores not found: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/processed/perplexity_scores.csv
- python code/correlation_analysis.py --threshold 0.9 & -> rc=1
    2026-06-29 03:58:13,196 - ERROR - Perplexity scores not found: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/processed/perplexity_scores.csv
- python code/quickstart_validation.py -> rc=1
    S
2026-06-29 03:58:13 - __main__ - INFO -   Documentation Validation: FAIL
2026-06-29 03:58:13 - __main__ - INFO -   Output Validation: PASS
2026-06-29 03:58:13 - __main__ - INFO -   Overall: FAIL
2026-06-29 03:58:13 - __main__ - INFO - ------------------------------------------------------------
2026-06-29 03:58:13 - __main__ - ERROR - Quickstart validation FAILED. Please review the errors above.

## Declared deliverables still missing

- data/analysis/correlation_results.csv
- data/raw/github-code-sample.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/visualization.py` — IS a run-book command
    - `code/correlation_analysis.py` — IS a run-book command
    - `code/checksum_correlation_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/github-code-sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/github-code-sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
