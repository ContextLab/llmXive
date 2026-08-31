# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/extraction/fetch_failure_handler.py: self-declared fabricated metric — “…data, mocks data, or returns placeholder values when a real fetch fails. All…”
- code/analysis/validate_bonferroni.py: synthetic/fake INPUT data not authorized by the spec — “…:     """     Generate a mock tract data structure for testing.…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…any fallback logic that generates synthetic data, mocks data, or ret…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…fallback to synthetic or mock data.     """     def __init_…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…ents any fallback     to synthetic data generation.          Arg…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…or synthetic data indicator (checked post-…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…ult looks like synthetic/fake data         # This is a safe…”
- code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…t accidentally returning mock data         if result is Non…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/extraction/fetch_failure_handler.py: self-declared fabricated metric — “…data, mocks data, or returns placeholder values when a real fetch fails. All…”; code/analysis/validate_bonferroni.py: synthetic/fake INPUT data not authorized by the spec — “…:     """     Generate a mock tract data structure for testing.…”; code/extraction/fetch_failure_handler.py: synthetic/fake INPUT data not authorized by the spec — “…any fallback logic that generates synthetic data, mocks data, or ret…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/data/generators.py --config default; 2 command(s) failed: python code/main.py --input data/raw/mock_studies.csv --output data/processed/meta_results.json (rc=1); python code/main.py --input data/raw/studies.csv --output data/processed/meta_results.json (rc=1); 11 declared deliverable(s) absent: data/derived/bonferroni_status.json; data/derived/forest_plot.png; data/derived/narrative_themes.json

## Failing / missing run-book commands

- python code/data/generators.py --config default -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/data/generators.py': [Errno 2] No such file or directory
- python code/main.py --input data/raw/mock_studies.csv --output data/processed/meta_results.json -> rc=1
    from analysis.meta_analysis import run_meta_analysis, main as run_meta_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/analysis/meta_analysis.py", line 17, in <module>
    from utils.logger import get_logger, log_error_context
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/utils/__init__.py", line 6, in <module>
    from .profiler import profile_pipeline_entrypoint, save_profile_results, run_profiler
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/utils/profiler.py", line 17, in <module>
    from main import run_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/main.py", line 10, in <module>
    from analysis.meta_analysis import run_meta_analysis, main as run_meta_main
ImportError: cannot import name 'run_meta_analysis' from partially initialized module 'analysis.meta_analysis' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/analysis/meta_analysis.py)
- python code/main.py --input data/raw/studies.csv --output data/processed/meta_results.json -> rc=1
    from analysis.meta_analysis import run_meta_analysis, main as run_meta_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/analysis/meta_analysis.py", line 17, in <module>
    from utils.logger import get_logger, log_error_context
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/utils/__init__.py", line 6, in <module>
    from .profiler import profile_pipeline_entrypoint, save_profile_results, run_profiler
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/utils/profiler.py", line 17, in <module>
    from main import run_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/main.py", line 10, in <module>
    from analysis.meta_analysis import run_meta_analysis, main as run_meta_main
ImportError: cannot import name 'run_meta_analysis' from partially initialized module 'analysis.meta_analysis' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-082-investigating-the-correlation-between-st/code/analysis/meta_analysis.py)

## Declared deliverables still missing

- data/derived/bonferroni_status.json
- data/derived/forest_plot.png
- data/derived/narrative_themes.json
- data/derived/results.json
- data/derived/tract_count.json
- data/logs/exclusion_log.csv
- data/processed/extracted_studies.csv
- data/processed/meta_status.json
- data/processed/study_count.json
- data/processed/valid_pair_count.json
- data/raw/studies.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/bonferroni_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correction.py` — NOT invoked by the run-book
    - `code/analysis/validate_bonferroni.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/bonferroni_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/forest_plot.png` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
    - `code/visualization/plots_forest.py` — NOT invoked by the run-book
    - `code/visualization/regenerator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/forest_plot.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/narrative_themes.json` is declared but was NOT written. Scripts referencing it:
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/narrative.py` — NOT invoked by the run-book
    - `code/analysis/narrative_logic.py` — NOT invoked by the run-book
    - `code/analysis/narrative_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/narrative_themes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/linting_runner.py` — NOT invoked by the run-book
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/tract_counting.py` — NOT invoked by the run-book
    - `code/analysis/bias.py` — NOT invoked by the run-book
    - `code/analysis/heterogeneity.py` — NOT invoked by the run-book
    - `code/analysis/meta_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/tract_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/tract_counting.py` — NOT invoked by the run-book
    - `code/analysis/correction.py` — NOT invoked by the run-book
    - `code/analysis/validate_bonferroni.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/tract_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/logs/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/extraction/parser.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/extracted_studies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/valid_pair_counter.py` — NOT invoked by the run-book
    - `code/analysis/study_counter.py` — NOT invoked by the run-book
    - `code/analysis/tract_counting.py` — NOT invoked by the run-book
    - `code/analysis/narrative_logic.py` — NOT invoked by the run-book
    - `code/analysis/heterogeneity.py` — NOT invoked by the run-book
    - `code/analysis/meta_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extracted_studies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/meta_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/meta_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/meta_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/study_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/narrative.py` — NOT invoked by the run-book
    - `code/analysis/study_counter.py` — NOT invoked by the run-book
    - `code/analysis/narrative_edge_case_handler.py` — NOT invoked by the run-book
    - `code/analysis/correction.py` — NOT invoked by the run-book
    - `code/analysis/narrative_engine.py` — NOT invoked by the run-book
    - `code/analysis/validate_bonferroni.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/study_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_pair_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/valid_pair_counter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_pair_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/studies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/valid_pair_counter.py` — NOT invoked by the run-book
    - `code/analysis/narrative.py` — NOT invoked by the run-book
    - `code/analysis/study_counter.py` — NOT invoked by the run-book
    - `code/analysis/tract_counting.py` — NOT invoked by the run-book
    - `code/analysis/narrative_edge_case_handler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/studies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
