# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/eval.py: self-declared fabricated metric — “…oss on the QNLI inputs)   * a dummy accuracy metric (token‑level match rat…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/results/training_summary_seed_0.json: metric is null/NaN (final_loss) — not a real measurement
- data/results/training_summary_seed_1.json: metric is null/NaN (final_loss) — not a real measurement
- data/results/training_summary_seed_2.json: metric is null/NaN (final_loss) — not a real measurement
- data/results/training_summary_seed_3.json: metric is null/NaN (final_loss) — not a real measurement
- data/results/training_summary_seed_4.json: metric is null/NaN (final_loss) — not a real measurement
- data/results/training_summary_seed_42.json: metric is null/NaN (final_loss) — not a real measurement

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/eval.py --results_dir data/results/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/eval.py: self-declared fabricated metric — “…oss on the QNLI inputs)   * a dummy accuracy metric (token‑level match rat…”; 6 hollow-result signal(s) — the analysis ran but computed nothing: data/results/training_summary_seed_0.json: metric is null/NaN (final_loss) — not a real measurement; data/results/training_summary_seed_1.json: metric is null/NaN (final_loss) — not a real measurement; data/results/training_summary_seed_2.json: metric is null/NaN (final_loss) — not a real measurement; 1 command(s) failed: python code/eval.py --results_dir data/results/ (rc=1)

## Failing / missing run-book commands

- python code/eval.py --results_dir data/results/ -> rc=1
kwargs.get("revision")).unresolve()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/huggingface_hub/hf_file_system.py", line 549, in resolve_path
    parsed = parse_hf_uri(f"{constants.HF_PROTOCOL}{path}")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 319, in parse_hf_uri
    return _parse_repo_body(location, type_, raw=raw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-589-dream-state-learning-implementing-rem-li/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 617, in _parse_repo_body
    raise HfUriError(uri=raw, msg=f"Repository id must be 'namespace/name', got '{repo_id}'.")
huggingface_hub.errors.HfUriError: Invalid HF URI 'hf://datasets/glue@bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/ax/test-*'. Repository id must be 'namespace/name', got 'glue'.

