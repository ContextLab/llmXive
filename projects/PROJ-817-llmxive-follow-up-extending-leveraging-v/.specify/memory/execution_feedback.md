# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (an initial subset of real prompts with row SHA-256 checksums) (rc=1); python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score) (rc=1); 1 declared deliverable(s) absent: data/raw/prompts_sample.parquet

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1
Collecting https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz

  ERROR: HTTP error 404 while getting https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz
ERROR: Could not install requirement https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz because of HTTP error 404 Client Error: Not Found for url: https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz for URL https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz

[notice] A new release of pip is available: 24.0 -> 26.2.1
[notice] To update, run: pip install --upgrade pip

- python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (an initial subset of real prompts with row SHA-256 checksums) -> rc=1
ption occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 231, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 188, in main
    df = collect_prompt_sample()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 147, in collect_prompt_sample
    for row in row_iter:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 87, in _iter_stream_hf
    yield from _iter_stream_hf_fallback()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-817-llmxive-follow-up-extending-leveraging-v/code/src/data/download.py", line 108, in _iter_stream_hf_fallback
    raise RuntimeError(
RuntimeError: Failed to fetch rows from HF API: status 422

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



## Declared deliverables still missing

- data/raw/prompts_sample.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/prompts_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download.py` — IS a run-book command
    - `code/tests/test_download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/prompts_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
