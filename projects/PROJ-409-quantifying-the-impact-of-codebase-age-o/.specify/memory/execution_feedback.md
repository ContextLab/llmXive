# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/inference/run_inference.py  --input data/extracted/snippets.csv  --output data/aggregated/file_metrics.csv  --timeout 300  --global-timeout 3600`
  - script usage: `run_inference.py [-h] --input-csv INPUT_CSV --output-csv OUTPUT_CSV`
  - argparse error: `run_inference.py: error: unrecognized arguments: --global-timeout 3600`
- run-book command: `python code/analysis/verify_report.py --input data/results/final_report.md`
  - script usage: `verify_report.py [-h] [--report-path REPORT_PATH]`
  - argparse error: `verify_report.py: error: unrecognized arguments: --input data/results/final_report.md`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/inference/model_downloader.py --model "Salesforce/codegen-350M-mono" --output data/models/; 11 command(s) failed: python code/setup_linting.py (rc=1); python code/extraction/run_extraction.py  --repos ""  --output data/extracted/snippets.csv (rc=1); python code/extraction/verify_extraction.py --input data/extracted/snippets.csv (rc=1); 1 declared deliverable(s) absent: data/aggregated/file_metrics.csv

## Failing / missing run-book commands

- python code/setup_linting.py -> rc=1
ite-packages/setuptools/build_meta.py", line 301, in _get_build_requires
          self.run_setup()
        File "/tmp/pip-build-env-vixid90_/overlay/lib/python3.11/site-packages/setuptools/build_meta.py", line 520, in run_setup
          super().run_setup(setup_script=setup_script)
        File "/tmp/pip-build-env-vixid90_/overlay/lib/python3.11/site-packages/setuptools/build_meta.py", line 317, in run_setup
          exec(code, locals())  # noqa: S102 # exec is intentional here
          ^^^^^^^^^^^^^^^^^^^^
        File "<string>", line 6, in <module>
        File "<frozen codecs>", line 918, in open
      FileNotFoundError: [Errno 2] No such file or directory: '/tmp/pip-install-0mz456uh/ast_00686d7a20b6440ba02dd476f11150db/AST/README'
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
error: subprocess-exited-with-error

× Getting requirements to build wheel did not run successfully.
│ exit code: 1
╰─> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.

[notice] A new release of pip is available: 24.0 -> 26.2.1
[notice] To update, run: pip install --upgrade pip

- python code/extraction/run_extraction.py  --repos ""  --output data/extracted/snippets.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/extraction/run_extraction.py", line 10, in <module>
    from extraction.git_utils import clone_repository, get_all_files_in_repo, calculate_median_commit_age
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/extraction/git_utils.py", line 9, in <module>
    from ..utils.logging import get_logger
ImportError: attempted relative import beyond top-level package

- python code/extraction/verify_extraction.py --input data/extracted/snippets.csv -> rc=1
2026-10-13 21:22:25 - __main__ - ERROR - Extraction output not found at data/extracted/snippets.csv. Please run code/extraction/run_extraction.py first.


- python code/inference/model_downloader.py --model "Salesforce/codegen-350M-mono" --output data/models/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-409-quantifying-the-impact-of-codebase-age-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/inference/model_downloader.py': [Errno 2] No such file or directory

- python code/inference/run_inference.py  --input data/extracted/snippets.csv  --output data/aggregated/file_metrics.csv  --timeout 300  --global-timeout 3600 -> rc=2

usage: run_inference.py [-h] --input-csv INPUT_CSV --output-csv OUTPUT_CSV
                        [--model-id MODEL_ID]
                        [--timeout-per-snippet TIMEOUT_PER_SNIPPET]
                        [--total-timeout TOTAL_TIMEOUT]
                        [--num-workers NUM_WORKERS]
run_inference.py: error: unrecognized arguments: --global-timeout 3600

- python code/inference/verify_inference_output.py --input data/aggregated/file_metrics.csv -> rc=1
2026-10-13 21:22:31 - __main__ - INFO - Verifying inference output CSV structure...
2026-10-13 21:22:31 - __main__ - ERROR - Inference Output file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/data/results/inference_results.csv
2026-10-13 21:22:31 - __main__ - INFO - Verifying file_metrics.csv structure...
2026-10-13 21:22:31 - __main__ - ERROR - File Metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/data/aggregated/file_metrics.csv
2026-10-13 21:22:31 - __main__ - ERROR - ❌ T019 Verification FAILED: One or more checks failed.


- python code/analysis/correlation.py  --input data/aggregated/file_metrics.csv  --output data/results/correlation_results.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/analysis/correlation.py", line 310, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/analysis/correlation.py", line 263, in main
    ensure_directories([output_path.parent])
TypeError: ensure_directories() takes 0 positional arguments but 1 was given

- python code/analysis/report_generator.py  --input data/results/correlation_results.csv  --output data/results/final_report.md -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/analysis/report_generator.py", line 6, in <module>
    from .correlation import load_file_metrics, filter_valid_rows, calculate_partial_correlation, run_correlation_analysis, save_results
ImportError: attempted relative import with no known parent package

- python code/analysis/verify_report.py --input data/results/final_report.md -> rc=2

usage: verify_report.py [-h] [--report-path REPORT_PATH]
verify_report.py: error: unrecognized arguments: --input data/results/final_report.md

- python code/utils/hasher.py  --file data/results/correlation_results.csv  --verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/utils/hasher.py", line 15, in <module>
    from .logging import get_logger
ImportError: attempted relative import with no known parent package

- python code/utils/reference_validator.py  --dir specs/001-quantify-age-impact/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/utils/reference_validator.py", line 13, in <module>
    from .logging import get_logger
ImportError: attempted relative import with no known parent package

- python code/extraction/run_extraction.py... -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-409-quantifying-the-impact-of-codebase-age-o/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-409-quantifying-the-impact-of-codebase-age-o/code/extraction/run_extraction.py...': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/aggregated/file_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/file_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — IS a run-book command
    - `code/analysis/report_generator.py` — IS a run-book command
    - `code/inference/verify_inference_output.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/file_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
