# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/preprocess.py: self-declared fabricated metric — “…lculation logic     # Returns dummy values for the sake of the logic fl…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…oading subject list from mock input: {mock_input_path}")…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…For now, we rely on the mock input as per task verification…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…mulate the process using mock input     # The actual downloa…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…# Since we are using mock input for verification, we ski…”
- code/graph_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…file is missing,     we generate a synthetic parcellation mask that m…”
- code/graph_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…reprocessed subjects (or mock data if none exist).     2. G…”
- code/graph_metrics.py: synthetic/fake INPUT data not authorized by the spec — “…bjects found. Generating mock data for verification.")…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/download.py --datasets ds000224 --sample-size 10`
  - script usage: `download.py [-h] [--mock-input MOCK_INPUT]`
  - argparse error: `download.py: error: unrecognized arguments: --datasets ds000224 --sample-size 10`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/preprocess.py: self-declared fabricated metric — “…lculation logic     # Returns dummy values for the sake of the logic fl…”; code/download.py: synthetic/fake INPUT data not authorized by the spec — “…oading subject list from mock input: {mock_input_path}")…”; code/download.py: synthetic/fake INPUT data not authorized by the spec — “…For now, we rely on the mock input as per task verification…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/hash_update.py --state state/projects/PROJ-216-exploring-the-relationship-between-brain.yaml; 4 command(s) failed: python code/download.py --datasets ds000224 --sample-size 10 (rc=2); python code/preprocess.py --input data/raw --output data/interim (rc=1); python code/graph_metrics.py --input data/interim --atlas Schaefer200 --output data/processed/metrics.csv (rc=1); 4 declared deliverable(s) absent: data/processed/analysis_resource_profile.json; data/processed/graph_metrics.csv; data/processed/preprocessing_stats.json

## Failing / missing run-book commands

- python code/download.py --datasets ds000224 --sample-size 10 -> rc=2
    usage: download.py [-h] [--mock-input MOCK_INPUT]
download.py: error: unrecognized arguments: --datasets ds000224 --sample-size 10
- python code/preprocess.py --input data/raw --output data/interim -> rc=1
    Warning: psutil not installed. Resource monitoring will be limited.
2026-08-26 16:44:15,682 - __main__ - ERROR - Valid subjects file not found. Run T015 first.
- python code/graph_metrics.py --input data/interim --atlas Schaefer200 --output data/processed/metrics.csv -> rc=1
    ndling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/graph_metrics.py", line 296, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/graph_metrics.py", line 275, in main
    metrics = compute_graph_metrics(sub, corr_mat)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/graph_metrics.py", line 213, in compute_graph_metrics
    "modularity_louvain_res1": compute_modularity_louvain(corr_matrix, resolution=1.0),
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/graph_metrics.py", line 172, in compute_modularity_louvain
    raise RuntimeError("The 'community' (python-louvain) package is required for modularity calculation.")
RuntimeError: The 'community' (python-louvain) package is required for modularity calculation.
- python code/stats.py --metrics data/processed/metrics.csv --behavioral data/processed/behavioral.csv --output reports/ -> rc=1
    Error: /home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/data/processed/graph_metrics.csv not found.
- python code/hash_update.py --state state/projects/PROJ-216-exploring-the-relationship-between-brain.yaml -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-216-exploring-the-relationship-between-brain/code/hash_update.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/analysis_resource_profile.json
- data/processed/graph_metrics.csv
- data/processed/preprocessing_stats.json
- data/processed/resource_profile.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_resource_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_analysis_resource_profile.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_resource_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graph_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/calculate_effect_sizes.py` — NOT invoked by the run-book
    - `code/graph_metrics.py` — IS a run-book command
    - `code/stats.py` — IS a run-book command
    - `code/generate_scatter_plots.py` — NOT invoked by the run-book
    - `code/merge_and_report_results.py` — NOT invoked by the run-book
    - `code/generate_summary_report.py` — NOT invoked by the run-book
    - `code/aggregate_graph_metrics.py` — NOT invoked by the run-book
    - `code/validate_graph_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graph_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/preprocessing_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_preprocessing_stats.py` — NOT invoked by the run-book
    - `code/verify_preprocessing_stats.py` — NOT invoked by the run-book
    - `code/calculate_preprocessing_success_rate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/preprocessing_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/resource_profile.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils.py` — IS a run-book command
    - `code/execute_resource_monitor.py` — NOT invoked by the run-book
    - `code/generate_analysis_resource_profile.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/resource_profile.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
