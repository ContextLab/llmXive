# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/setup_data_structure.py: self-declared fabricated metric — “…s is REAL data structure, not fake values)     # Source: https://surve…”; 2 command(s) failed: python code/data/download.py (rc=1); python code/main.py (rc=1); 7 declared deliverable(s) absent: data/processed/cluster_alignment.json; data/processed/cluster_results.json; data/processed/confidence_interval.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
- __main__ - INFO - Attempting to fetch from Stack Overflow archive: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z
2026-10-17 10:19:49,175 - __main__ - WARNING - URL returned non-200 status: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z (Status: 404)
2026-10-17 10:19:49,176 - __main__ - WARNING - Primary URL not reachable (Status: 404)
2026-10-17 10:19:49,176 - __main__ - INFO - Primary source failed, attempting HuggingFace fallback...
2026-10-17 10:19:49,176 - __main__ - INFO - Attempting to load dataset from HuggingFace: stack-exchange/stackoverflow
2026-10-17 10:19:49,402 - __main__ - ERROR - Error during HuggingFace fetch: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-17 10:19:49,402 - __main__ - ERROR - Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed.
2026-10-17 10:19:49,402 - __main__ - ERROR - Download failed: Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed.

- python code/main.py -> rc=1
tch from Stack Overflow archive: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z
2026-10-17 10:19:49,903 - data.download - WARNING - URL returned non-200 status: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z (Status: 404)
2026-10-17 10:19:49,904 - data.download - WARNING - Primary URL not reachable (Status: 404)
2026-10-17 10:19:49,904 - data.download - INFO - Primary source failed, attempting HuggingFace fallback...
2026-10-17 10:19:49,904 - data.download - INFO - Attempting to load dataset from HuggingFace: stack-exchange/stackoverflow
2026-10-17 10:19:50,099 - data.download - ERROR - Error during HuggingFace fetch: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-17 10:19:50,099 - data.download - ERROR - Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed.
2026-10-17 10:19:50,099 - data.download - ERROR - Download failed: Primary Stack Overflow dump URL unreachable: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.7z. HF fallback also failed or unavailable. Cannot proceed.



## Declared deliverables still missing

- data/processed/cluster_alignment.json
- data/processed/cluster_results.json
- data/processed/confidence_interval.json
- data/processed/external_metrics.json
- data/processed/tag_mappings.json
- data/processed/trend_intermediate.json
- data/processed/trend_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cluster_alignment.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_alignment.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cluster_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_cluster_results.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/confidence_interval.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/confidence_interval.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/mapping.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tag_mappings.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/mapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tag_mappings.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_intermediate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/trends.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_intermediate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trend_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bootstrapping.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/generate_trend_results.py` — NOT invoked by the run-book
    - `code/analysis/linting_config.py` — NOT invoked by the run-book
    - `code/data/external.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/run_quickstart.py` — NOT invoked by the run-book
    - `code/verification/verify_limitations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trend_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
