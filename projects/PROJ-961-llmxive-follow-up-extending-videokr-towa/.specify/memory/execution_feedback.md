# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…Checking {t013_path} for synthetic data fallbacks...")     if t0…”
- code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…tions.append(f"Potential synthetic data usage found: {line.strip…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…at {log_path}. Skipping synthetic data check via this path.")…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…"     Check for signs of synthetic data fallback in the annotati…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…xplicit flags indicating synthetic data usage (though the     co…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…should raise an error if synthetic data is used, this is a sanit…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…d earlier if it tried to generate synthetic data.         logger.inf…”
- code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…# 4. Check Synthetic Data Fallback         synthet…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…Checking {t013_path} for synthetic data fallbacks...")     if t0…”; code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…tions.append(f"Potential synthetic data usage found: {line.strip…”; code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…at {log_path}. Skipping synthetic data check via this path.")…”; 4 command(s) failed: python code/main.py (rc=1); python code/ingest/annotate_graph.py (rc=1); python -m pytest tests/unit/test_graph_utils.py (rc=1); 14 declared deliverable(s) absent: data/processed/accuracy_binned.png; data/processed/accuracy_vs_hop_raw.csv; data/processed/accuracy_vs_hop_raw.png

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/main.py", line 120, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/main.py", line 24, in main
    processed_dir = get_path(project_root, "processed_data")
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given

- python code/ingest/annotate_graph.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/ingest/annotate_graph.py", line 177, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/ingest/annotate_graph.py", line 122, in main
    raw_dir = get_path(project_root, "raw_data")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given

- python -m pytest tests/unit/test_graph_utils.py -> rc=1
hop_distance(graph, 'A', 'Z') # Z not in graph
>       self.assertEqual(dist, -1)
E       AssertionError: None != -1

tests/unit/test_graph_utils.py:108: AssertionError
___________________ TestGraphUtils.test_get_hop_distribution ___________________

self = <tests.unit.test_graph_utils.TestGraphUtils testMethod=test_get_hop_distribution>

    def test_get_hop_distribution(self):
        """Test hop distribution calculation."""
        edges = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
            ('D', 'E')
        ]
        graph = build_undirected_graph(edges)
    
        # Distribution of shortest paths from 'A'
        dist = get_hop_distribution(graph, 'A')
    
>       self.assertIn(0, dist) # A to A
        ^^^^^^^^^^^^^^^^^^^^^^
E       AssertionError: 0 not found in {}

tests/unit/test_graph_utils.py:140: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_graph_utils.py::TestGraphUtils::test_calculate_hop_distance
FAILED tests/unit/test_graph_utils.py::TestGraphUtils::test_get_hop_distribution
========================= 2 failed, 6 passed in 0.20s ==========================


- python -m pytest tests/integration/test_pipeline.py -> rc=2
=
_ ERROR collecting projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/tests/integration/test_pipeline.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/tests/integration/test_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_pipeline.py:23: in <module>
    from analysis.detect_threshold import (
E   ImportError: cannot import name 'load_binned_accuracy_data' from 'analysis.detect_threshold' (/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/analysis/detect_threshold.py)
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.37s ===============================



## Declared deliverables still missing

- data/processed/accuracy_binned.png
- data/processed/accuracy_vs_hop_raw.csv
- data/processed/accuracy_vs_hop_raw.png
- data/processed/annotated_videokr.csv
- data/processed/annotation_coverage.json
- data/processed/bin_config.json
- data/processed/memory_log.json
- data/processed/removal_validation.json
- data/processed/runtime_log.json
- data/processed/sensitivity_intermediate.json
- data/processed/sensitivity_overlay.png
- data/processed/sensitivity_thresholds.csv
- data/processed/stability_metric.json
- data/processed/threshold_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/accuracy_binned.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_binned_summary.py` — NOT invoked by the run-book
    - `code/analysis/visualize_continuous.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/accuracy_binned.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/accuracy_vs_hop_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_continuous_plot.py` — NOT invoked by the run-book
    - `code/analysis/generate_continuous_plot_data.py` — NOT invoked by the run-book
    - `code/analysis/visualize_continuous.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/accuracy_vs_hop_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/accuracy_vs_hop_raw.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_continuous_plot.py` — NOT invoked by the run-book
    - `code/analysis/generate_continuous_plot_data.py` — NOT invoked by the run-book
    - `code/analysis/visualize_continuous.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/accuracy_vs_hop_raw.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/annotated_videokr.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/fit_gam.py` — NOT invoked by the run-book
    - `code/analysis/generate_continuous_plot_data.py` — NOT invoked by the run-book
    - `code/analysis/plot_sensitivity_overlay.py` — NOT invoked by the run-book
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/analysis/visualize_continuous.py` — NOT invoked by the run-book
    - `code/ingest/annotate_graph.py` — IS a run-book command
    - `code/ingest/calculate_annotation_coverage.py` — NOT invoked by the run-book
    - `code/ingest/verify_annotation_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/annotated_videokr.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/annotation_coverage.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/ingest/calculate_annotation_coverage.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/annotation_coverage.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bin_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bin_utils.py` — NOT invoked by the run-book
    - `code/analysis/detect_threshold.py` — IS a run-book command
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_summary.py` — NOT invoked by the run-book
    - `code/analysis/generate_threshold_results.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bin_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/memory_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/memory_logger.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/removal_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/verify_t080.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/removal_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/runtime_logger.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_overlay.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plot_sensitivity_overlay.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_overlay.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_thresholds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_summary.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_table.py` — NOT invoked by the run-book
    - `code/analysis/generate_stability_metric.py` — NOT invoked by the run-book
    - `code/analysis/plot_sensitivity_overlay.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_thresholds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stability_metric.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_sensitivity_summary.py` — NOT invoked by the run-book
    - `code/analysis/generate_stability_metric.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stability_metric.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_threshold_results.py` — NOT invoked by the run-book
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
