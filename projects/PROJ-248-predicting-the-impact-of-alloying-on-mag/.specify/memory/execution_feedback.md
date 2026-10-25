# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_datasets.py (rc=1); python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs (rc=1); python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json (rc=1); 1 declared deliverable(s) absent: data/raw_oqmd.csv

## Failing / missing run-book commands

- python code/download_datasets.py -> rc=1
ack (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 216, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 201, in main
    mp_manifest = download_materials_project(raw_mp_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 119, in download_materials_project
    for record in _stream_mp_records():
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/code/download_datasets.py", line 84, in _stream_mp_records
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://next-gen.materialsproject.org/rest/v2/materials/search?has_magnetic_properties=true&limit=1000&skip=0

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
