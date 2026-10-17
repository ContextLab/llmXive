# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (first 2,000 real prompts with row SHA-256 checksums)`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (first 2,000 real prompts with row SHA-256 checksums) (rc=1); python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score) (rc=1); 1 declared deliverable(s) absent: data/raw/prompts_sample.parquet

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1
python3.11/site-packages/spacy/errors.py", line 3, in <module>
    from .compat import Literal
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/spacy/compat.py", line 39, in <module>
    from thinc.api import Optimizer  # noqa: F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/thinc/api.py", line 1, in <module>
    from .backends import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/thinc/backends/__init__.py", line 17, in <module>
    from .cupy_ops import CupyOps
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/thinc/backends/cupy_ops.py", line 16, in <module>
    from .numpy_ops import NumpyOps
  File "thinc/backends/numpy_ops.pyx", line 1, in init thinc.backends.numpy_ops
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject

- python -m code.src.data.download           # streams the real InstructPix2Pix train split; writes data/raw/prompts_sample.parquet (first 2,000 real prompts with row SHA-256 checksums) -> rc=1
^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/datasets/load.py", line 2606, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/datasets/load.py", line 2277, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/datasets/load.py", line 1917, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/lib/python3.11/site-packages/datasets/load.py", line 1867, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'timbrooks/instructpix2pix' doesn't exist on the Hub or cannot be accessed.

- python -m code.src.data.curate             # creates data/results/curated_prompts.csv (adds synthetic_score) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named code.src.data.curate

- python -m code.src.data.conflict_generator # injects contradictions into neutral prompts → conflicting set -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named code.src.data.conflict_generator

- python -m code.src.data.human_annotation   # launches a lightweight web form or MTurk batch for **all 1000 prompts** -> rc=1

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
