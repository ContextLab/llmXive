# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…_metrics.json) using the mock data defined in the task spec…”
- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…ll pipeline by using the mock data that the unit tests rely…”
- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…metrics, save_metrics  # Mock data matching the test file M…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script`
  - script usage: `01_data_curation.py [-h] [--curate] [--tag]`
  - argparse error: `01_data_curation.py: error: unrecognized arguments: # Assuming tagging is integrated or in a separate script`
- run-book command: `python code/utils/matching.py # Or the designated matching script`
  - script usage: `matching.py [-h] [--input INPUT] [--output OUTPUT]`
  - argparse error: `matching.py: error: unrecognized arguments: # Or the designated matching script`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…_metrics.json) using the mock data defined in the task spec…”; scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…ll pipeline by using the mock data that the unit tests rely…”; scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…metrics, save_metrics  # Mock data matching the test file M…”; 7 command(s) failed: python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script (rc=2); python code/utils/matching.py # Or the designated matching script (rc=2); python code/02_metric_extraction.py (rc=1); 10 declared deliverable(s) absent: data/ground_truth/classifier_metrics.json; data/logs/refactor_validation_report.json; data/logs/repo_exclusions.csv

## Failing / missing run-book commands

- python code/01_data_curation.py --tag # Assuming tagging is integrated or in a separate script -> rc=2

None of PyTorch, TensorFlow >= 2.0, or Flax have been found. Models won't be available and only tokenizers, configuration and file/data utilities can be used.
usage: 01_data_curation.py [-h] [--curate] [--tag]
01_data_curation.py: error: unrecognized arguments: # Assuming tagging is integrated or in a separate script

- python code/utils/matching.py # Or the designated matching script -> rc=2

usage: matching.py [-h] [--input INPUT] [--output OUTPUT]
                   [--repo-metadata REPO_METADATA]
                   [--log-level {DEBUG,INFO,WARNING,ERROR}]
matching.py: error: unrecognized arguments: # Or the designated matching script

- python code/02_metric_extraction.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/02_metric_extraction.py", line 18, in <module>
    from utils.logging_config import get_logger, setup_logging
ImportError: cannot import name 'get_logger' from 'utils.logging_config' (/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/utils/logging_config.py)

- python code/03_analysis.py -> rc=1
/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 317, in main
    pairs_df = load_matched_pairs()
               ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 48, in load_matched_pairs
    raise FileNotFoundError(f"Required file not found: {path}")
FileNotFoundError: Required file not found: data/processed/matched_pairs_filtered.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 365, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 317, in main
    pairs_df = load_matched_pairs()
               ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_analysis.py", line 48, in load_matched_pairs
    raise FileNotFoundError(f"Required file not found: {path}")
FileNotFoundError: Required file not found: data/processed/matched_pairs_filtered.csv

- python code/03_visualization.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/03_visualization.py", line 17, in <module>
    from utils.logging_config import get_logger, setup_logging
ImportError: cannot import name 'get_logger' from 'utils.logging_config' (/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/utils/logging_config.py)

- python code/04_ground_truth_selection.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/04_ground_truth_selection.py", line 14, in <module>
    from utils.logging_config import get_logger, setup_logging
ImportError: cannot import name 'get_logger' from 'utils.logging_config' (/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/utils/logging_config.py)

- python -m pytest tests/ -> rc=2
hon names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_repo_filtering.py:17: in <module>
    from utils.repo_filter import (
code/utils/repo_filter.py:19: in <module>
    from utils.logging_config import get_logger
E   ImportError: cannot import name 'get_logger' from 'utils.logging_config' (/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/utils/logging_config.py)
=========================== short test summary info ============================
ERROR tests/unit/test_01_data_curation.py
ERROR tests/unit/test_05_classifier_evaluation.py
ERROR tests/unit/test_bug_fix_latency.py
ERROR tests/unit/test_checksum_generation.py
ERROR tests/unit/test_classifier_metrics.py
ERROR tests/unit/test_code_block_extraction.py
ERROR tests/unit/test_repo_deletion_handling.py
ERROR tests/unit/test_repo_filter.py
ERROR tests/unit/test_repo_filtering.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 1.49s ===============================



## Declared deliverables still missing

- data/ground_truth/classifier_metrics.json
- data/logs/refactor_validation_report.json
- data/logs/repo_exclusions.csv
- data/processed/matched_pairs.csv
- data/processed/matched_pairs_filtered.csv
- data/processed/metrics_longitudinal.csv
- data/processed/tagged_blocks.csv
- data/raw/code_blocks.csv
- data/raw/repo_list.csv
- data/raw/repo_metadata.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/ground_truth/classifier_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
    - `code/08_classifier_threshold_validation.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `scripts/run_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/ground_truth/classifier_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/refactor_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/git_mv_detector.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/refactor_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/repo_exclusions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/repo_exclusions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/04_ground_truth_selection.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_longitudinal.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_edge_case_handler.py` — NOT invoked by the run-book
    - `code/02_metric_extraction.py` — IS a run-book command
    - `code/02_metric_validation.py` — NOT invoked by the run-book
    - `code/03_analysis.py` — IS a run-book command
    - `code/03_visualization.py` — IS a run-book command
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_longitudinal.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tagged_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tagged_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/code_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
    - `code/utils/git_mv_detector.py` — NOT invoked by the run-book
    - `code/utils/matching.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/code_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/repo_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_curation.py` — IS a run-book command
    - `code/utils/matching.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/repo_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
