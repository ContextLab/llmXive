# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”
- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…())                  # Return placeholder result         return EvaluationResu…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…synthetic_generator.py # Synthetic dataset generation │   └── downl…”
- code/baselines/arima.py: synthetic/fake INPUT data not authorized by the spec — “…_baseline(config)      # Generate synthetic time series     np.rando…”
- code/baselines/moving_average.py: synthetic/fake INPUT data not authorized by the spec — “…_baseline(config)      # Generate synthetic time series with anomali…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Anomaly Dataset Generator for Time Serie…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ly Detection Validation  Generates synthetic time series data with kn…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…et:     """Container for generated synthetic dataset with metadata.""…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/results/download_manifest.json, data/raw/nab_ambient_temperature.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05`
  - script usage: `synthetic_generator.py [-h] [--output OUTPUT] [--length LENGTH]`
  - argparse error: `synthetic_generator.py: error: unrecognized arguments: --anomaly-rate 0.05`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 77 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”; code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…())                  # Return placeholder result         return EvaluationResu…”; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…synthetic_generator.py # Synthetic dataset generation │   └── downl…”; every produced artifact is gitignored (data/processed/results/download_manifest.json, data/raw/nab_ambient_temperature.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/src/config.py --check (rc=1); python code/src/data/download_datasets.py (rc=1); python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 (rc=2); 1 declared deliverable(s) absent: data/processed/results/data_checksums.json

## Failing / missing run-book commands

- python code/src/config.py --check -> rc=1
============================================================
Configuration Check
============================================================
ERROR: Configuration file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/code/config.yaml


- python code/src/data/download_datasets.py -> rc=1
nomaly-dete/code/src/data/download_datasets.py", line 174, in write_download_manifest
    json.dump(manifest, f, indent=2, sort_keys=True)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 432, in _iterencode
    yield from _iterencode_dict(o, _current_indent_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 439, in _iterencode
    o = _default(o)
        ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type PosixPath is not JSON serializable

- python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 -> rc=2

usage: synthetic_generator.py [-h] [--output OUTPUT] [--length LENGTH]
                              [--anomaly-type {point,contextual,collective}]
                              [--seed SEED]
synthetic_generator.py: error: unrecognized arguments: --anomaly-rate 0.05

- python code/src/services/anomaly_detector.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 21, in <module>
    from models.dpgmm import DPGMMModel, DPGMMConfig
ModuleNotFoundError: No module named 'models.dpgmm'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 24, in <module>
    from ..models.dpgmm import DPGMMModel, DPGMMConfig
ImportError: attempted relative import with no known parent package

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 28, in <module>
    from models.dpgmm import DPGMMModel, DPGMMConfig
ModuleNotFoundError: No module named 'models.dpgmm'

- python code/src/evaluation/simulation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py", line 33, in <module>
    from code.src.data.windowing import SlidingWindowExtractor
ImportError: cannot import name 'SlidingWindowExtractor' from 'code.src.data.windowing' (/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/windowing.py)

- python code/src/evaluation/robustness.py --subset-size 50 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/robustness.py", line 32, in <module>
    from models.dp_gmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/dp_gmm.py", line 21, in <module>
    from models.anomaly_score import AnomalyScore
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 8, in <module>
    class AnomalyScore:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/models/anomaly_score.py", line 27, in AnomalyScore
    component_assignments: Optional[List[int]] = field(default=None)
                                    ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?


## Declared deliverables still missing

- data/processed/results/data_checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/results/data_checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_checksums.py` — NOT invoked by the run-book
    - `code/scripts/generate_data_checksums.py` — NOT invoked by the run-book
    - `code/scripts/verify_state_checksums.py` — NOT invoked by the run-book
    - `code/src/data/download_datasets.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/results/data_checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
