# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/entropy.py: function `execute_and_compare` returns a bare RNG draw (line 55) — a reported value computed from no real input

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/src/data_loader.py --download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/entropy.py: function `execute_and_compare` returns a bare RNG draw (line 55) — a reported value computed from no real input; 6 command(s) failed: python code/src/data_loader.py --download (rc=1); python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50 (rc=1); python code/src/inference.py --output data/processed/convergence_results.csv --sample-size 50 (rc=1); 4 declared deliverable(s) absent: data/processed/convergence_results.csv; data/processed/entropy_results.csv; data/processed/exclusion_log.json

## Failing / missing run-book commands

- python code/src/data_loader.py --download -> rc=1
    ath(url_or_filename)
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/huggingface_hub/hf_file_system.py", line 305, in resolve_path
    parsed = parse_hf_uri(f"{constants.HF_PROTOCOL}{path}")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 319, in parse_hf_uri
    return _parse_repo_body(location, type_, raw=raw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 617, in _parse_repo_body
    raise HfUriError(uri=raw, msg=f"Repository id must be 'namespace/name', got '{repo_id}'.")
huggingface_hub.errors.HfUriError: Invalid HF URI 'hf://datasets/openai_humaneval@7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544/.huggingface.yaml'. Repository id must be 'namespace/name', got 'openai_humaneval'.
- python code/src/entropy.py --output data/processed/entropy_results.csv --sample-size 50 -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/inference.py --output data/processed/convergence_results.csv --sample-size 50 -> rc=1
    2026-07-24 07:35:11,219 - __main__ - INFO - Loading model: codellama/CodeLlama-1.3b-Instruct-hf on cpu
2026-07-24 07:35:11,322 - httpx - INFO - HTTP Request: HEAD https://huggingface.co/codellama/CodeLlama-1.3b-Instruct-hf/resolve/main/config.json "HTTP/1.1 401 Unauthorized"
2026-07-24 07:35:11,398 - httpx - INFO - HTTP Request: HEAD https://huggingface.co/codellama/CodeLlama-1.3b-Instruct-hf/resolve/main/config.json "HTTP/1.1 401 Unauthorized"
2026-07-24 07:35:11,398 - __main__ - ERROR - Failed to load model: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2026-07-24 07:35:11,398 - __main__ - ERROR - No processed dataset found at /home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/data/processed/humaneval_processed.csv or alternatives.
- python code/src/entropy.py --output data/processed/entropy_results.csv -> rc=1
    ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/configuration_utils.py", line 776, in _get_config_dict
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/.venv/lib/python3.11/site-packages/transformers/utils/hub.py", line 469, in cached_files
    raise OSError(
OSError: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
- python code/src/inference.py --output data/processed/convergence_results.csv -> rc=1
    2026-07-24 07:35:23,181 - __main__ - INFO - Loading model: codellama/CodeLlama-1.3b-Instruct-hf on cpu
2026-07-24 07:35:23,298 - httpx - INFO - HTTP Request: HEAD https://huggingface.co/codellama/CodeLlama-1.3b-Instruct-hf/resolve/main/config.json "HTTP/1.1 401 Unauthorized"
2026-07-24 07:35:23,377 - httpx - INFO - HTTP Request: HEAD https://huggingface.co/codellama/CodeLlama-1.3b-Instruct-hf/resolve/main/config.json "HTTP/1.1 401 Unauthorized"
2026-07-24 07:35:23,377 - __main__ - ERROR - Failed to load model: codellama/CodeLlama-1.3b-Instruct-hf is not a local folder and is not a valid model identifier listed on 'https://huggingface.co/models'
If this is a private repository, make sure to pass a token having permission to this repo either by logging in with `hf auth login` or by passing `token=<your_token>`
2026-07-24 07:35:23,378 - __main__ - ERROR - No processed dataset found at /home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/data/processed/humaneval_processed.csv or alternatives.
- python code/src/analysis.py --entropy data/processed/entropy_results.csv  --convergence data/processed/convergence_results.csv  --output data/processed/router_simulation.csv -> rc=1
    2026-07-24 07:35:25,568 - __main__ - INFO - Starting router training analysis...
2026-07-24 07:35:25,569 - __main__ - ERROR - Analysis failed: Entropy results not found at data/processed/entropy_results.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 337, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 329, in main
    model, metrics = run_analysis()
                     ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 235, in run_analysis
    entropy_results = load_entropy_results()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/code/src/analysis.py", line 31, in load_entropy_results
    raise FileNotFoundError(f"Entropy results not found at {ENTROPY_RESULTS_PATH}")
FileNotFoundError: Entropy results not found at data/processed/entropy_results.csv

## Declared deliverables still missing

- data/processed/convergence_results.csv
- data/processed/entropy_results.csv
- data/processed/exclusion_log.json
- data/processed/resource_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/convergence_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_logging_utils.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
    - `code/tests/test_router_evaluation.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/tests/test_flops_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_model_pilot.py` — NOT invoked by the run-book
    - `code/src/logging_utils.py` — NOT invoked by the run-book
    - `code/src/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/convergence_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_logging_utils.py` — NOT invoked by the run-book
    - `code/tests/test_robustness.py` — NOT invoked by the run-book
    - `code/tests/test_analysis.py` — NOT invoked by the run-book
    - `code/scripts/run_model_pilot.py` — NOT invoked by the run-book
    - `code/src/logging_utils.py` — NOT invoked by the run-book
    - `code/src/analysis.py` — IS a run-book command
    - `code/src/model_pilot.py` — NOT invoked by the run-book
    - `code/src/entropy.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/entropy_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/logging_utils.py` — NOT invoked by the run-book
    - `code/src/entropy.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/resource_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/inference.py` — IS a run-book command
    - `code/src/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/resource_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/entropy_results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/test_logging_utils.py`, `code/tests/test_robustness.py`, `code/src/analysis.py`, `code/src/model_pilot.py`, `code/src/entropy.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/entropy_results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/tests/test_logging_utils.py`, `code/tests/test_robustness.py`, `code/src/analysis.py`, `code/src/model_pilot.py`, `code/src/entropy.py`.
