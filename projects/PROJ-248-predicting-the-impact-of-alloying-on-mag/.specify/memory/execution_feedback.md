# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_datasets.py (rc=1); python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs (rc=1); python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json (rc=1); 1 declared deliverable(s) absent: data/raw_oqmd.csv

## Failing / missing run-book commands

- python code/download_datasets.py -> rc=1
y", line 89, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 3285, in dataset_info
    hf_raise_for_status(r)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 953, in hf_raise_for_status
    raise _format(RepositoryNotFoundError, message, response, repo_type=repo_type, repo_id=repo_id) from e
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6adca28d-24ad4f6611a0dbb81e75bfdb;19f76a0d-e860-40d6-833c-3c014d5c5720)

Repository Not Found for url: https://huggingface.co/api/datasets/materialsproject/materialsproject/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

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
