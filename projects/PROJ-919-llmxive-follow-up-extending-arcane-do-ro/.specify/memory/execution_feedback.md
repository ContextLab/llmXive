# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/services/judge_service.py: self-declared fabricated metric — “…l.     # For now, we return a dummy score and flag based on simple heur…”
- src/scripts/generate_gold_standard.py: function `generate_ground_truth_score` returns a bare RNG draw (line 24) — a reported value computed from no real input
- code/src/services/probe_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ine (T019 Demo)")      # Mock data for demonstration     mo…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/gold_standard/human_annotations.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/services/judge_service.py: self-declared fabricated metric — “…l.     # For now, we return a dummy score and flag based on simple heur…”; src/scripts/generate_gold_standard.py: function `generate_ground_truth_score` returns a bare RNG draw (line 24) — a reported value computed from no real input; code/src/services/probe_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ine (T019 Demo)")      # Mock data for demonstration     mo…”; every produced artifact is gitignored (data/gold_standard/human_annotations.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python -m src.cli.download_text --character "Elizabeth Bennet" (rc=1); python -m src.cli.axis_input --coarse-file path/to/coarse.json --fine-file path/to/fine.json (rc=1); python -m src.cli.generate_probes --character "Elizabeth Bennet" --output data/derived/probes.jsonl (rc=1)

## Failing / missing run-book commands

- python -m src.cli.download_text --character "Elizabeth Bennet" -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/.venv/bin/python: No module named src.cli.download_text

- python -m src.cli.axis_input --coarse-file path/to/coarse.json --fine-file path/to/fine.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/src/cli/axis_input.py", line 10, in <module>
    from src.lib.utils import get_logger
ModuleNotFoundError: No module named 'src.lib'

- python -m src.cli.generate_probes --character "Elizabeth Bennet" --output data/derived/probes.jsonl -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/.venv/bin/python: No module named src.cli.generate_probes

- python -m src.cli.run_experiment -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/src/cli/run_experiment.py", line 14, in <module>
    from src.lib.utils import get_logger
ModuleNotFoundError: No module named 'src.lib'

- python -m src.cli.check_data_integrity -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/.venv/bin/python: No module named src.cli.check_data_integrity

- python -m src.cli.run_experiment -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-919-llmxive-follow-up-extending-arcane-do-ro/code/src/cli/run_experiment.py", line 14, in <module>
    from src.lib.utils import get_logger
ModuleNotFoundError: No module named 'src.lib'

