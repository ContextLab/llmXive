# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_datasets.py (rc=1); python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs (rc=1); python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json (rc=1); 1 declared deliverable(s) absent: data/raw_oqmd.csv

## Failing / missing run-book commands

- python code/download_datasets.py -> rc=1
 main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 108, in main
    mp_manifest = download_materials_project(raw_mp_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 64, in download_materials_project
    df.to_json(raw_mp_path, orient="records", lines=True, force_ascii=False)
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/util/_decorators.py", line 333, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/generic.py", line 2702, in to_json
    return json.to_json(
           ^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/json/_json.py", line 210, in to_json
    ).write()
      ^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/json/_json.py", line 263, in write
    return ujson_dumps(
           ^^^^^^^^^^^^
OverflowError: Maximum recursion level reached

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
