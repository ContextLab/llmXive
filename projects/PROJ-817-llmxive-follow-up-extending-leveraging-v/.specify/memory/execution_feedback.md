# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (an initial subset of real prompts with row SHA-256 checksums) (rc=1); python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score) (rc=1)

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named spacy

- python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (an initial subset of real prompts with row SHA-256 checksums) -> rc=1
_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 325, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 283, in main
    df = collect_prompt_sample()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 224, in collect_prompt_sample
    for row in row_iter:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 161, in _iter_rows_api
    resp.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url: https://datasets-server.huggingface.co/rows?dataset=timbrooks%2Finstructpix2pix&config=default&split=train&offset=0&length=100

- python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named code.src.data.curate

- python -m code.src.data.conflict_generator # injects contradictions into neutral prompts → conflicting set -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named code.src.data.conflict_generator

- python -m code.src.data.human_annotation   # launches a lightweight web form or MTurk batch for the full set of prompts -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named code.src.data.human_annotation

- python -m code.src.parser.graph_builder     # reads data/results/curated_prompts.csv, writes JSON graphs to data/results/graphs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'code.src.parser.graph_builder' (ModuleNotFoundError: No module named 'code.src.parser')

- python -m code.src.verifier.baseline        # produces data/results/baseline_scores.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'code.src.verifier.baseline' (ModuleNotFoundError: No module named 'code.src.verifier')

- python -m code.src.verifier.augmented       # produces data/results/augmented_scores.csv and control condition files -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'code.src.verifier.augmented' (ModuleNotFoundError: No module named 'code.src.verifier')

- python -m code.src.analysis.stats           # runs paired tests (conflicting & neutral), control comparison, robustness check, correlation, correction -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'code.src.analysis.stats' (ModuleNotFoundError: No module named 'code.src.analysis')

- python -m code.src.analysis.report          # writes data/results/report.json and report.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'code.src.analysis.report' (ModuleNotFoundError: No module named 'code.src.analysis')

- python -m pytest code/tests/test_evaluation_report.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_evaluation_report.py


