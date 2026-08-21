# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”
- code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data_loader.py --download`
- `python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv`
- `python code/runner.py --strategy Greedy --input data/processed/graphs/graph_clean.json --output data/processed/results/greedy_results.csv --topk 5`
- `python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7`
- `python code/runner.py --strategy Lazy --input data/processed/graphs/graph_noise_42.json --output data/processed/results/lazy_noisy_results.csv --threshold 0.7`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv`
  - script usage: `runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'Full' (choose from 'full', 'lazy', 'greedy')`
- run-book command: `python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7`
  - script usage: `runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'Lazy' (choose from 'full', 'lazy', 'greedy')`
- run-book command: `python code/runner.py --strategy Greedy --input data/processed/graphs/graph_clean.json --output data/processed/results/greedy_results.csv --topk 5`
  - script usage: `runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'Greedy' (choose from 'full', 'lazy', 'greedy')`
- run-book command: `python code/runner.py --strategy Lazy --input data/processed/graphs/graph_noise_42.json --output data/processed/results/lazy_noisy_results.csv --threshold 0.7`
  - script usage: `runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]`
  - argparse error: `runner.py: error: argument --strategy: invalid choice: 'Lazy' (choose from 'full', 'lazy', 'greedy')`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…rategy.  This script: 1. Generates a synthetic memory graph of varying…”; code/benchmark_full_traversal.py: synthetic/fake INPUT data not authorized by the spec — “…nx.DiGraph:     """     Generates a synthetic directed graph for bench…”; every produced artifact is gitignored (data/processed/stats_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/data_loader.py --download (rc=1); python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv (rc=2); python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7 (rc=2); 11 declared deliverable(s) absent: data/intermediate/graphs_raw.json; data/processed/baseline_results.csv; data/processed/correlation_results.json

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'locomo/locomo-benchmark' doesn't exist on the Hub or cannot be accessed.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 445, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 403, in main
    tasks = fetch_locomo_dataset(subset=args.subset)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py", line 72, in fetch_locomo_dataset
    raise ValueError("Dataset fetch failed") from e
ValueError: Dataset fetch failed
- python code/runner.py --strategy Full --input data/processed/graphs/graph_clean.json --output data/processed/results/baseline_results.csv -> rc=2
    usage: runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]
                 [--timeout TIMEOUT] [--strategy {full,lazy,greedy}]
                 [--output OUTPUT] [--subset SUBSET]
runner.py: error: argument --strategy: invalid choice: 'Full' (choose from 'full', 'lazy', 'greedy')
- python code/runner.py --strategy Lazy --input data/processed/graphs/graph_clean.json --output data/processed/results/lazy_results.csv --threshold 0.7 -> rc=2
    usage: runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]
                 [--timeout TIMEOUT] [--strategy {full,lazy,greedy}]
                 [--output OUTPUT] [--subset SUBSET]
runner.py: error: argument --strategy: invalid choice: 'Lazy' (choose from 'full', 'lazy', 'greedy')
- python code/runner.py --strategy Greedy --input data/processed/graphs/graph_clean.json --output data/processed/results/greedy_results.csv --topk 5 -> rc=2
    usage: runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]
                 [--timeout TIMEOUT] [--strategy {full,lazy,greedy}]
                 [--output OUTPUT] [--subset SUBSET]
runner.py: error: argument --strategy: invalid choice: 'Greedy' (choose from 'full', 'lazy', 'greedy')
- python code/runner.py --strategy Lazy --input data/processed/graphs/graph_noise_42.json --output data/processed/results/lazy_noisy_results.csv --threshold 0.7 -> rc=2
    usage: runner.py [-h] [--streaming] [--chunk-size CHUNK_SIZE]
                 [--timeout TIMEOUT] [--strategy {full,lazy,greedy}]
                 [--output OUTPUT] [--subset SUBSET]
runner.py: error: argument --strategy: invalid choice: 'Lazy' (choose from 'full', 'lazy', 'greedy')

## Declared deliverables still missing

- data/intermediate/graphs_raw.json
- data/processed/baseline_results.csv
- data/processed/correlation_results.json
- data/processed/graphs/graph_noise_42.json
- data/processed/greedy_results.csv
- data/processed/lazy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/noisy_greedy_results.csv
- data/processed/noisy_lazy_results.csv
- data/processed/sensitivity_analysis.csv
- data/processed/threshold_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/graphs_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/graphs_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graphs/graph_noise_42.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/strategies/lazy_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
    - `code/utils/generate_audit_report.py` — NOT invoked by the run-book
    - `code/utils/verify_seeds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graphs/graph_noise_42.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
    - `code/strategies/greedy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/strategies/lazy_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_baseline_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_baseline_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_baseline_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_greedy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_greedy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_greedy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/noisy_lazy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/noisy_stats.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — IS a run-book command
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/strategies/noisy_lazy_runner.py` — NOT invoked by the run-book
    - `code/utils/validate_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/noisy_lazy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/strategies/lazy.py` — NOT invoked by the run-book
    - `code/strategies/sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
