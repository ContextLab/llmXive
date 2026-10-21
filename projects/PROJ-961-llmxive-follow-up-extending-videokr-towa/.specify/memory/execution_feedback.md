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

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/checksums.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…Checking {t013_path} for synthetic data fallbacks...")     if t0…”; code/analysis/compliance_check_removed.py: synthetic/fake INPUT data not authorized by the spec — “…tions.append(f"Potential synthetic data usage found: {line.strip…”; code/analysis/resource_constraint_audit.py: synthetic/fake INPUT data not authorized by the spec — “…at {log_path}. Skipping synthetic data check via this path.")…”; every produced artifact is gitignored (data/raw/checksums.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/analysis/power_analysis.py; python code/analysis/model_lrt.py; 4 command(s) failed: python code/main.py (rc=1); python code/ingest/annotate_graph.py (rc=1); python -m pytest tests/unit/ (rc=2); 9 declared deliverable(s) absent: data/processed/accuracy_binned.png; data/processed/accuracy_vs_hop_raw.csv; data/processed/accuracy_vs_hop_raw.png

## Failing / missing run-book commands

- python code/main.py -> rc=1

2026-10-21 22:15:22,264 - INFO - Pipeline started
2026-10-21 22:15:22,264 - INFO - Running T013: Annotate graph...
2026-10-21 22:15:22,927 - ERROR - Data files not found. Run download_data.py first.

- python code/ingest/annotate_graph.py -> rc=1

2026-10-21 22:15:23,299 - ERROR - Data files not found. Run download_data.py first.

- python code/analysis/power_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-961-llmxive-follow-up-extending-videokr-towa/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/analysis/power_analysis.py': [Errno 2] No such file or directory

- python code/analysis/model_lrt.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-961-llmxive-follow-up-extending-videokr-towa/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/analysis/model_lrt.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
r-towa/tests/unit/test_t021_small_bin_handling.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/tests/unit/test_t021_small_bin_handling.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_t021_small_bin_handling.py:3: in <module>
    from code.analysis.detect_threshold import detect_threshold, MIN_BIN_SIZE
E   ImportError: cannot import name 'MIN_BIN_SIZE' from 'code.analysis.detect_threshold' (/home/runner/work/llmXive/llmXive/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa/code/analysis/detect_threshold.py)
=========================== short test summary info ============================
ERROR tests/unit/test_sensitivity.py
ERROR tests/unit/test_setup_directories.py
ERROR tests/unit/test_t021_small_bin_handling.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.50s ===============================


- python -m pytest tests/integration/ -> rc=2
tlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/integration/test_t021_small_bins.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 0.74s ========================



## Declared deliverables still missing

- data/processed/accuracy_binned.png
- data/processed/accuracy_vs_hop_raw.csv
- data/processed/accuracy_vs_hop_raw.png
- data/processed/annotated_videokr.csv
- data/processed/annotation_coverage.json
- data/processed/memory_log.json
- data/processed/runtime_log.json
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
- `data/processed/memory_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/memory_logger.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/resource_constraint_audit.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/runtime_logger.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
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
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
