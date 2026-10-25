# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_datasets.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_datasets.py (rc=1); python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs (rc=1); python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json (rc=1); 1 declared deliverable(s) absent: data/raw_oqmd.csv

## Failing / missing run-book commands

- python code/download_datasets.py -> rc=1
oad.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'materialsproject/mp-2020.10.01' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 154, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 140, in main
    mp_manifest = download_materials_project(raw_mp_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 64, in download_materials_project
    raise RuntimeError(f"Materials Project dataset not accessible: {e}")
RuntimeError: Materials Project dataset not accessible: Dataset 'materialsproject/mp-2020.10.01' doesn't exist on the Hub or cannot be accessed.

- python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src')

- python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/bin/python: Error while finding module specification for 'src.cli.predict' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/raw_oqmd.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw_oqmd.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_datasets.py` — IS a run-book command
  Make ONE of these WRITE `data/raw_oqmd.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
