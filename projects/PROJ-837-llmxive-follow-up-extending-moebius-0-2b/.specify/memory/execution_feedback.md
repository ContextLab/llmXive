# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/annotator.py: metric `score` assigned from an RNG draw (line 188)
- code/eval/ablation_runner.py: self-declared fabricated metric — “…e": np.random.uniform(1, 5) # Simulated score for binning         })…”
- code/eval/inference_runner.py: self-declared fabricated metric — “…bins.         # This is NOT a fake measurement, but a fake label assignment…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/mask_generator.py --seed <random_seed>`
  - script usage: `mask_generator.py [-h] [--seed SEED] [--sample-size SAMPLE_SIZE]`
  - argparse error: `mask_generator.py: error: argument --seed: invalid int value: '<random_seed>'`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/annotator.py: metric `score` assigned from an RNG draw (line 188); code/eval/ablation_runner.py: self-declared fabricated metric — “…e": np.random.uniform(1, 5) # Simulated score for binning         })…”; code/eval/inference_runner.py: self-declared fabricated metric — “…bins.         # This is NOT a fake measurement, but a fake label assignment…”; 6 command(s) failed: python code/data/download.py (rc=1); python code/data/mask_generator.py --seed <random_seed> (rc=2); python code/data/annotator.py --participants --seed 42 (rc=1); 10 declared deliverable(s) absent: data/annotations/decoupled_scores.csv; data/annotations/human_scores.csv; data/annotations/krippendorff_raw.json

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    [2026-10-01 04:54:13] Downloading Places365 subset (limit=100)...
[2026-10-01 04:54:13] Failed to download dataset: fetch_places365_subset() got an unexpected keyword argument 'limit'
- python code/data/mask_generator.py --seed <random_seed> -> rc=2
    usage: mask_generator.py [-h] [--seed SEED] [--sample-size SAMPLE_SIZE]
                         [--output-dir OUTPUT_DIR]
mask_generator.py: error: argument --seed: invalid int value: '<random_seed>'
- python code/data/annotator.py --participants --seed 42 -> rc=1
    [2026-10-01 04:54:18] Starting Research Mode workflow.
[2026-10-01 04:54:18] Research mode disabled: Human annotation file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/annotations/human_scores.csv
[2026-10-01 04:54:18] Validation failed: Human Annotation Load - Human annotation file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/annotations/human_scores.csv
[2026-10-01 04:54:18] Research Mode validation failed.
- python code/training/train_gating.py --epochs [REDACTED] -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/training/train_gating.py", line 35, in <module>
    logger = setup_project_logger("train_gating")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/utils/logger.py", line 43, in setup_project_logger
    return get_logger(name, str(log_file))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/utils/logger.py", line 32, in get_logger
    os.makedirs(os.dirname(log_file), exist_ok=True)
                ^^^^^^^^^^
AttributeError: module 'os' has no attribute 'dirname'
- python code/training/train_end_to_end.py --epochs [a sufficient number of] -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/training/train_end_to_end.py", line 35, in <module>
    logger = setup_project_logger("train_end_to_end")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/utils/logger.py", line 43, in setup_project_logger
    return get_logger(name, str(log_file))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/utils/logger.py", line 32, in get_logger
    os.makedirs(os.dirname(log_file), exist_ok=True)
                ^^^^^^^^^^
AttributeError: module 'os' has no attribute 'dirname'
- python code/eval/evaluate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/eval/evaluate.py", line 15, in <module>
    from eval.metrics import run_metrics_evaluation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/eval/metrics.py", line 21, in <module>
    from torchmetrics.image import FrechetInceptionDistance
ImportError: cannot import name 'FrechetInceptionDistance' from 'torchmetrics.image' (/home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/.venv/lib/python3.11/site-packages/torchmetrics/image/__init__.py)

## Declared deliverables still missing

- data/annotations/decoupled_scores.csv
- data/annotations/human_scores.csv
- data/annotations/krippendorff_raw.json
- data/processed/mask_metrics.json
- data/results/ablation_report.json
- data/results/evaluation_report.json
- data/results/latency_raw.csv
- data/results/permutation_test.json
- data/results/power_analysis.json
- data/results/proxy_validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/annotations/decoupled_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/training/train_gating.py` — IS a run-book command
    - `code/eval/inference_runner.py` — NOT invoked by the run-book
    - `code/eval/gate.py` — NOT invoked by the run-book
    - `code/eval/stats.py` — NOT invoked by the run-book
    - `code/data/persistor.py` — NOT invoked by the run-book
    - `code/data/annotator.py` — IS a run-book command
    - `code/data/validate_and_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/decoupled_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/annotations/human_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/training/train_gating.py` — IS a run-book command
    - `code/eval/gate.py` — NOT invoked by the run-book
    - `code/eval/stats.py` — NOT invoked by the run-book
    - `code/data/persistor.py` — NOT invoked by the run-book
    - `code/data/annotator.py` — IS a run-book command
    - `code/data/validate_and_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/human_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/annotations/krippendorff_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/eval/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/annotations/krippendorff_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mask_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/training/train_gating.py` — IS a run-book command
    - `code/eval/gate.py` — NOT invoked by the run-book
    - `code/eval/stats.py` — NOT invoked by the run-book
    - `code/data/annotator.py` — IS a run-book command
    - `code/data/mask_generator.py` — IS a run-book command
    - `code/data/validate_and_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mask_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/ablation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/ablation_overhead.py` — NOT invoked by the run-book
    - `code/eval/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ablation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/evaluation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/report.py` — NOT invoked by the run-book
    - `code/eval/verify_target.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/evaluation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/latency_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/ablation_overhead.py` — NOT invoked by the run-book
    - `code/eval/inference_runner.py` — NOT invoked by the run-book
    - `code/eval/report.py` — NOT invoked by the run-book
    - `code/eval/ablation_runner.py` — NOT invoked by the run-book
    - `code/eval/verify_target.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/latency_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_test.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_test.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/eval/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/proxy_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/gate.py` — NOT invoked by the run-book
    - `code/eval/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/proxy_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/annotations/human_scores.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/utils/quickstart_validator.py`, `code/training/train_gating.py`, `code/eval/gate.py`, `code/eval/stats.py`, `code/data/persistor.py`, `code/data/annotator.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/annotations/human_scores.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/utils/quickstart_validator.py`, `code/training/train_gating.py`, `code/eval/gate.py`, `code/eval/stats.py`, `code/data/persistor.py`, `code/data/annotator.py`, `code/data/validate_and_log.py`.
