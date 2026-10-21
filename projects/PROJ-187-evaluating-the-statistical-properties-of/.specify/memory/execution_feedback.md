# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/cli/run_fidelity.py: self-declared fabricated metric — “…)     log.info("Full pipeline placeholder metric results written to %s", metri…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/adult/holdout.parquet, data/processed/adult/train.parquet, data/raw/adult/raw.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: src/cli/run_fidelity.py: self-declared fabricated metric — “…)     log.info("Full pipeline placeholder metric results written to %s", metri…”; every produced artifact is gitignored (data/processed/adult/holdout.parquet, data/processed/adult/train.parquet, data/raw/adult/raw.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python -m src.cli.run_fidelity --smoke (rc=1); python -m src.cli.run_fidelity --full  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 (rc=1); python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity --smoke -> rc=1
  df[col].fillna(mode, inplace=True)
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 192, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 177, in main
    _run_smoke()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 59, in _run_smoke
    csv_path = generate_and_save(
               ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/models/synthesize.py", line 53, in generate_and_save
    synth_df = train_model(
               ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/models/trainer.py", line 94, in train_model
    ModelClass = sdv.tabular.CTGAN
                 ^^^^^^^^^^^
AttributeError: module 'sdv' has no attribute 'tabular'

- python -m src.cli.run_fidelity --full  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 -> rc=1
he operation inplace on the original object.


  df[col].fillna(mode, inplace=True)
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 192, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 179, in main
    _run_full(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 118, in _run_full
    generate_and_save(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/models/synthesize.py", line 53, in generate_and_save
    synth_df = train_model(
               ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/models/trainer.py", line 94, in train_model
    ModelClass = sdv.tabular.CTGAN
                 ^^^^^^^^^^^
AttributeError: module 'sdv' has no attribute 'tabular'

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def schema():
        if not SCHEMA_YAML.is_file():
>           pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
E           Failed: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-statistical-fidelity/contracts/metric_results.schema.yaml

tests/contract/test_metric_schema.py:39: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.32s


