# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py  --max-samples 5000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01 (rc=1)

## Failing / missing run-book commands

- python code/main.py  --max-samples 5000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01 -> rc=1
projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 155, in download_file
    response.raise_for_status()  # Raise HTTPError for bad status
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/matminer/matminer-data/master/oqmd/oqmd.csv

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 350, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 209, in main
    download_all()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 243, in download_all
    raise RuntimeError(f"Dataset download failed for '{dataset_id}'") from e
RuntimeError: Dataset download failed for 'band_gap'

