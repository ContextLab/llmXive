# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv`
  - script usage: `python -m code.run_experiments [-h] [--config CONFIG]`
  - argparse error: `python -m code.run_experiments: error: unrecognized arguments: --mode fixed --rhos 0.1 0.3 0.5 0.7 0.9 --seeds 42 43 44 --output outputs/fixed_baselines.csv`
- run-book command: `python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json`
  - script usage: `python -m code.run_experiments [-h] [--config CONFIG]`
  - argparse error: `python -m code.run_experiments: error: unrecognized arguments: --mode adaptive --seeds 42 43 44 --output outputs/adaptive_run.json`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data.py --download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data.py --download (rc=1); python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv (rc=2); python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json (rc=2)

## Failing / missing run-book commands

- python code/data.py --download -> rc=1
k/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 210, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 204, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 153, in download_all
    n_gsm = _snapshot_to_jsonl(load_gsm8k(split="test", streaming=True), gsm8k_path)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 129, in _snapshot_to_jsonl
    for row in iterable:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 58, in _fetch_jsonl
    raise RuntimeError(
RuntimeError: Failed to download openai/gsm8k/main from https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test.jsonl: 404 Client Error: Not Found for url: https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test.jsonl

- python -m code.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv -> rc=2

usage: python -m code.run_experiments [-h] [--config CONFIG]
                                      [--stage {adaptive_runs,analysis,data,fixed_baselines,model}]
                                      [--seed SEED] [--dry-run]
python -m code.run_experiments: error: unrecognized arguments: --mode fixed --rhos 0.1 0.3 0.5 0.7 0.9 --seeds 42 43 44 --output outputs/fixed_baselines.csv

- python -m code.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json -> rc=2

usage: python -m code.run_experiments [-h] [--config CONFIG]
                                      [--stage {adaptive_runs,analysis,data,fixed_baselines,model}]
                                      [--seed SEED] [--dry-run]
python -m code.run_experiments: error: unrecognized arguments: --mode adaptive --seeds 42 43 44 --output outputs/adaptive_run.json

- python -m code.analysis  --fixed outputs/fixed_baselines.csv  --adaptive outputs/adaptive_run.json  --outdir outputs/statistics -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: No module named code.analysis

