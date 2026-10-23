# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/synthetic_meta.csv, data/raw/tide.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/synthetic_meta.csv, data/raw/tide.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 12 command(s) failed: python -m src.data.acquire_real   # creates data/raw/tide.parquet, verifies SHA‑256, writes data/raw/tide.csv and data/raw/tide.sha256 (rc=1); python -m src.features.extract   # reads all .py files, writes data/features.csv (includes origin + sha256) (rc=1); python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (includes origin) (rc=1)

## Failing / missing run-book commands

- python -m src.data.acquire_real   # creates data/raw/tide.parquet, verifies SHA‑256, writes data/raw/tide.csv and data/raw/tide.sha256 -> rc=1
IDE dataset acquisition.
2026-10-23 03:09:22,810 INFO __main__: Downloading Parquet from https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/data/test-00000-of-00001-9189dc62872204f7.parquet
2026-10-23 03:09:24,051 INFO __main__: Wrote Parquet checksum to '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/data/raw/tide.sha256'
2026-10-23 03:09:24,087 INFO __main__: Converting Parquet to CSV at '/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/data/raw/tide.csv'
2026-10-23 03:09:24,142 INFO __main__: Renaming columns {'ground_truth_label': 'label'} to match required schema.
2026-10-23 03:09:24,142 ERROR __main__: Acquisition failed
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/data/acquire_real.py", line 226, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/data/acquire_real.py", line 198, in main
    raise RuntimeError(
RuntimeError: Parquet file is missing required columns after renaming: {'instance_id'}

- python -m src.features.extract   # reads all .py files, writes data/features.csv (includes origin + sha256) -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/features/extract.py", line 238, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/features/extract.py", line 161, in main
    raise FileNotFoundError(f"Real TIDE CSV not found at {tide_csv}")
FileNotFoundError: Real TIDE CSV not found at /home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/data/raw/tide.csv

- python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (includes origin) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_lite' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv (includes origin) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_original' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.consolidate   # creates data/merged_results.csv (SSoT, retains origin) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.consolidate' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.data.split_data          # writes train_ids.txt & val_ids.txt (seed=42) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: No module named src.data.split_data

- python -m src.analysis.logistic        # logistic regression, EPV check, interaction handling, bootstrap CI -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.logistic' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.mcnemar         # stratified 3×3 McNemar tests + Holm‑Bonferroni -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.mcnemar' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.sensitivity     # probability‑cutoff, synthetic‑parameter, and binning‑scheme sweeps -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.sensitivity' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.efficiency      # total runtime & CPU utilisation check -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.efficiency' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.visualize   # writes PNGs under outputs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.visualize' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


