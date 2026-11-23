# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/stats_engine.py: synthetic/fake INPUT data not authorized by the spec — “…ames for unit‑tests that generate synthetic data. """  import os imp…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/stats_engine.py: synthetic/fake INPUT data not authorized by the spec — “…ames for unit‑tests that generate synthetic data. """  import os imp…”; 5 command(s) failed: python -m pytest tests/test_fetcher.py -v (rc=1); python -m pytest tests/test_stats_engine.py -v (rc=1); python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) (rc=4); 7 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/graph_metrics.csv; data/processed/mdes_report.json

## Failing / missing run-book commands

- python -m pytest tests/test_fetcher.py -v -> rc=1
operties (qubits, '
                                                  'gates, measurements)',
                                   'type': 'object'},
                    'timestamp': {'description': 'ISO 8601 timestamp of '
                                                 'the calibration snapshot',
                                  'format': 'date-time',
                                  'type': 'string'}},
     'required': ['device_id', 'timestamp', 'coupling_map', 'properties'],
     'type': 'object'}

On instance:
    {'chip_family': 'Falcon',
     'coupling_map': [[0, 1]],
     'device_id': 'test_dev',
     'gates': [{'gate': 'cx',
                'parameters': [{'name': 'gate_error', 'value': 0.01},
                               {'name': 'readout_error', 'value': 0.02}]}],
     'qubits': [[{'name': 'T1', 'value': 0.0001},
                 {'name': 'T2', 'value': 5e-05}],
                [{'name': 'T1', 'value': 0.00011},
                 {'name': 'T2', 'value': 6e-05}]],
     'timestamp': '2026-10-16T22:11:23.483859+00:00'}
FAILED tests/test_fetcher.py::test_no_synthetic_fallback - SystemExit: 2
========================= 2 failed, 2 passed in 1.34s ==========================


- python -m pytest tests/test_stats_engine.py -v -> rc=1
on undefined for t2_mean vs clustering_coeff (constant input).
WARNING  code.stats_engine:stats_engine.py:150 Spearman correlation undefined for cx_error_mean vs readout_error_mean (constant input).
WARNING  code.stats_engine:stats_engine.py:150 Spearman correlation undefined for readout_error_mean vs avg_shortest_path (constant input).
WARNING  code.stats_engine:stats_engine.py:150 Spearman correlation undefined for readout_error_mean vs clustering_coeff (constant input).
=============================== warnings summary ===============================
tests/test_stats_engine.py: 18 warnings
  /home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/stats_engine.py:147: ConstantInputWarning: An input array is constant; the correlation coefficient is not defined.
    rho, p_val = spearmanr(valid[col_a], valid[col_b])

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_stats_engine.py::test_apply_benjamini_hochberg_fdr - assert np.True_ is True
=================== 1 failed, 2 passed, 18 warnings in 0.72s ===================


- python -m pytest tests/test_integration_fetch.py -v   # live API (rate‑limited) -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-163-exploring-the-role-of-network-structure-/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-
configfile: pyproject.toml
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 233, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 229, in main
    generate_graph_metrics_csv(args.raw_dir, out_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 165, in generate_graph_metrics_csv
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
  File "<frozen os>", line 225, in makedirs
FileNotFoundError: [Errno 2] No such file or directory: ''

- python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 233, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 229, in main
    generate_graph_metrics_csv(args.raw_dir, out_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-163-exploring-the-role-of-network-structure-/code/graph_builder.py", line 165, in generate_graph_metrics_csv
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
  File "<frozen os>", line 225, in makedirs
FileNotFoundError: [Errno 2] No such file or directory: ''


## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/graph_metrics.csv
- data/processed/mdes_report.json
- data/processed/partial_correlations.csv
- data/processed/performance_metrics.csv
- data/processed/robustness_results.csv
- figures/correlation_heatmap.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/run_robustness.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/generate_graph_metrics_csv.py` — NOT invoked by the run-book
    - `code/graph_builder.py` — IS a run-book command
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_graph_builder.py` — NOT invoked by the run-book
    - `code/tests/test_partial_corr.py` — NOT invoked by the run-book
    - `code/tests/test_robustness_lodo.py` — NOT invoked by the run-book
    - `code/tests/test_stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mdes_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_mdes_report_section.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mdes_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/partial_correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_partial_corr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/partial_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fetcher.py` — NOT invoked by the run-book
    - `code/generate_calibration_csv.py` — NOT invoked by the run-book
    - `code/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/process_raw.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_partial_corr.py` — NOT invoked by the run-book
    - `code/tests/test_process_raw.py` — NOT invoked by the run-book
    - `code/tests/test_processed_csv.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_robustness.py` — NOT invoked by the run-book
    - `code/stats_engine.py` — NOT invoked by the run-book
    - `code/tests/test_robustness_lodo.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/correlation_heatmap.png` is declared but was NOT written. Scripts referencing it:
    - `code/viz.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/correlation_heatmap.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
