# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/02_classification.py: synthetic/fake INPUT data not authorized by the spec — “…oes **not** fall back to synthetic data.  If any required resour…”
- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…_metrics.json) using the mock data defined in the task spec…”
- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…ll pipeline by using the mock data that the unit tests rely…”
- scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…metrics, save_metrics  # Mock data matching the test file M…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/02_classification.py: synthetic/fake INPUT data not authorized by the spec — “…oes **not** fall back to synthetic data.  If any required resour…”; scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…_metrics.json) using the mock data defined in the task spec…”; scripts/run_classifier_evaluation.py: synthetic/fake INPUT data not authorized by the spec — “…ll pipeline by using the mock data that the unit tests rely…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py   # orchestrates all steps in order; 1 command(s) failed: python -m pytest tests/contract/ (rc=1); 8 declared deliverable(s) absent: data/analysis/power_analysis_a_priori.json; data/ground_truth/classifier_metrics.json; data/logs/repo_exclusions.csv

## Failing / missing run-book commands

- python code/main.py   # orchestrates all steps in order -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-247-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-247-evaluating-the-impact-of-code-generation/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
v'

tests/contract/test_metrics_schema.py:74: FileNotFoundError
____________________ test_metrics_longitudinal_valid_labels ____________________

    def test_metrics_longitudinal_valid_labels():
        """Test that labels are either 'LLM' or 'Human'."""
        output_path = Path("data/processed/metrics_longitudinal.csv")
        valid_labels = {'LLM', 'Human'}
>       with open(output_path, 'r', newline='', encoding='utf-8') as f:
E       FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/metrics_longitudinal.csv'

tests/contract/test_metrics_schema.py:85: FileNotFoundError
=========================== short test summary info ============================
FAILED tests/contract/test_metrics_schema.py::test_metrics_longitudinal_schema_exists
FAILED tests/contract/test_metrics_schema.py::test_metrics_longitudinal_has_correct_headers
FAILED tests/contract/test_metrics_schema.py::test_metrics_longitudinal_data_types
FAILED tests/contract/test_metrics_schema.py::test_metrics_longitudinal_no_duplicates
FAILED tests/contract/test_metrics_schema.py::test_metrics_longitudinal_valid_labels
============================== 5 failed in 0.04s ===============================



## Declared deliverables still missing

- data/analysis/power_analysis_a_priori.json
- data/ground_truth/classifier_metrics.json
- data/logs/repo_exclusions.csv
- data/processed/matched_pairs.csv
- data/processed/matched_pairs_filtered.csv
- data/processed/metrics_longitudinal.csv
- data/processed/tagged_blocks.csv
- data/raw/code_blocks.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/power_analysis_a_priori.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis_a_priori.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/ground_truth/classifier_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_analysis.py` — NOT invoked by the run-book
    - `code/03_visualization.py` — NOT invoked by the run-book
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
    - `code/08_classifier_threshold_validation.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `scripts/run_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/ground_truth/classifier_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/logs/repo_exclusions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/repo_exclusions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — NOT invoked by the run-book
    - `code/03_analysis.py` — NOT invoked by the run-book
    - `code/03_visualization.py` — NOT invoked by the run-book
    - `code/04_ground_truth_selection.py` — NOT invoked by the run-book
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/matched_pairs_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_extraction.py` — NOT invoked by the run-book
    - `code/03_analysis.py` — NOT invoked by the run-book
    - `code/16_repo_filtering.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/utils/repo_filter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/matched_pairs_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_longitudinal.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_metric_edge_case_handler.py` — NOT invoked by the run-book
    - `code/02_metric_extraction.py` — NOT invoked by the run-book
    - `code/02_metric_validation.py` — NOT invoked by the run-book
    - `code/03_analysis.py` — NOT invoked by the run-book
    - `code/03_visualization.py` — NOT invoked by the run-book
    - `code/07_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/09_power_analysis.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_longitudinal.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tagged_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_classification.py` — NOT invoked by the run-book
    - `code/05_classifier_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tagged_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/code_blocks.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_classification.py` — NOT invoked by the run-book
    - `code/03_code_block_extraction.py` — NOT invoked by the run-book
    - `code/utils/matching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/code_blocks.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
