# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…s that zero synthetic or mock data sources were loaded duri…”
- code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…rds indicating synthetic/mock data usage.          Args:…”
- code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…("CRITICAL: Synthetic or mock data sources detected in pipe…”
- code/062c_mock_data_flow_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…:     """     Ensure the mock data directory structure exis…”
- code/062c_mock_data_flow_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…ignal_path}")      # 10. Mock eQTL data (T045 output)     eqtl_p…”
- code/062c_mock_data_flow_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Created mock eQTL data: {eqtl_path}")  def run_…”
- code/062c_mock_data_flow_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…"description": "Mock Data Flow Simulation",…”
- code/062c_mock_data_flow_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Mock Data Flow Simulation for T62c…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 12 fabricated/simulated-result signal(s) — results are not real measurements: code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…s that zero synthetic or mock data sources were loaded duri…”; code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…rds indicating synthetic/mock data usage.          Args:…”; code/04_filter.py: synthetic/fake INPUT data not authorized by the spec — “…("CRITICAL: Synthetic or mock data sources detected in pipe…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/05_weights.py; 3 command(s) failed: python code/03_annotate.py (rc=1); python code/04_filter.py (rc=1); python code/08_visualize.py (rc=1); 6 declared deliverable(s) absent: data/processed/cre_filtered.tsv; data/processed/delta_peak_signal.tsv; data/processed/hic_validation_flags.tsv

## Failing / missing run-book commands

- python code/03_annotate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/03_annotate.py", line 18, in <module>
    import pybedtools
ModuleNotFoundError: No module named 'pybedtools'
- python code/04_filter.py -> rc=1
    2026-10-01T23:08:08 - INFO - Starting data integrity assertion scan on: logs/pipeline.log
2026-10-01T23:08:08 - ERROR - Log file not found: logs/pipeline.log
2026-10-01T23:08:08 - CRITICAL - Integrity check failed: Log file logs/pipeline.log does not exist. Cannot verify data source integrity.
- python code/05_weights.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/05_weights.py': [Errno 2] No such file or directory
- python code/08_visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/code/08_visualize.py", line 37, in <module>
    logging.FileHandler('logs/pipeline.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-153-decoding-regulatory-element-contribution/logs/pipeline.log'

## Declared deliverables still missing

- data/processed/cre_filtered.tsv
- data/processed/delta_peak_signal.tsv
- data/processed/hic_validation_flags.tsv
- data/processed/lmm_results.tsv
- data/processed/peak_signal_matrix.tsv
- data/processed/vif_flags.tsv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cre_filtered.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062c_mock_data_flow_simulation.py` — NOT invoked by the run-book
    - `code/051b_filter_genes.py` — NOT invoked by the run-book
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cre_filtered.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/delta_peak_signal.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062c_mock_data_flow_simulation.py` — NOT invoked by the run-book
    - `code/05b_compute_delta_signal.py` — NOT invoked by the run-book
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — IS a run-book command
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
    - `code/05_validate_cre_gating.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/delta_peak_signal.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/hic_validation_flags.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062c_mock_data_flow_simulation.py` — NOT invoked by the run-book
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/hic_validation_flags.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lmm_results.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lmm_results.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/peak_signal_matrix.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062c_mock_data_flow_simulation.py` — NOT invoked by the run-book
    - `code/05b_check_collinearity.py` — NOT invoked by the run-book
    - `code/05b_compute_delta_signal.py` — NOT invoked by the run-book
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/peak_signal_matrix.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_flags.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/062c_mock_data_flow_simulation.py` — NOT invoked by the run-book
    - `code/05b_check_collinearity.py` — NOT invoked by the run-book
    - `code/062b_path_dependency_checker.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — IS a run-book command
    - `code/05c_compute_weights.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_flags.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
