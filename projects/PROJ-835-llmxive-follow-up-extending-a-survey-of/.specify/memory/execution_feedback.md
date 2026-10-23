# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/data/extract.py; 3 command(s) failed: python code/data/download.py (rc=1); python code/src/models/train.py (rc=1); python code/tests/integration/test_eval_correlation.py (rc=1); 2 declared deliverable(s) absent: data/anomaly_scores.parquet; data/embeddings.parquet

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/__init__.py", line 46, in <module>
    from pandas.core.api import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/core/api.py", line 1, in <module>
    from pandas._libs import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/_libs/__init__.py", line 18, in <module>
    from pandas._libs.interval import Interval
  File "interval.pyx", line 1, in init pandas._libs.interval
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject

- python code/data/extract.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/data/extract.py': [Errno 2] No such file or directory

- python code/src/models/train.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/src/models/train.py", line 10, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/__init__.py", line 46, in <module>
    from pandas.core.api import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/core/api.py", line 1, in <module>
    from pandas._libs import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/_libs/__init__.py", line 18, in <module>
    from pandas._libs.interval import Interval
  File "interval.pyx", line 1, in init pandas._libs.interval
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject

- python code/tests/integration/test_eval_correlation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/tests/integration/test_eval_correlation.py", line 8, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/__init__.py", line 46, in <module>
    from pandas.core.api import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/core/api.py", line 1, in <module>
    from pandas._libs import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-835-llmxive-follow-up-extending-a-survey-of/lib/python3.11/site-packages/pandas/_libs/__init__.py", line 18, in <module>
    from pandas._libs.interval import Interval
  File "interval.pyx", line 1, in init pandas._libs.interval
ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject


## Declared deliverables still missing

- data/anomaly_scores.parquet
- data/embeddings.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **1495** real records with fields: index, goal, category, prompt, response, speech_path, response_audio_path, attack_type, target_model, platform, source, behavior.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

# Load the dataset with a specific configuration
ds = datasets.load_dataset("MBZUAI/AudioJailbreak", name="Origin")

# Determine total number of records across all splits
if isinstance(ds, dict):
    total_records = sum(len(split) for split in ds.values())
    # Use a sample from the first available split
    first_split = next(iter(ds.values()))
    sample = first_split[0]
else:
    total_records = len(ds)
    sample = ds[0]

# Extract field names from the sample record
fields = list(sample.keys())

print(f"RECORDS={total_records}")
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/anomaly_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/cli/update_state.py` — NOT invoked by the run-book
    - `code/src/models/baseline_noise.py` — NOT invoked by the run-book
    - `code/src/models/eval.py` — NOT invoked by the run-book
    - `code/src/models/report_generator.py` — NOT invoked by the run-book
    - `code/src/models/train.py` — IS a run-book command
    - `code/tests/integration/test_eval_correlation.py` — IS a run-book command
    - `src/models/eval.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/anomaly_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/embeddings.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/setup_data_structure.py` — NOT invoked by the run-book
    - `code/setup_project_structure.py` — NOT invoked by the run-book
    - `code/src/cli/update_state.py` — NOT invoked by the run-book
    - `code/src/data/embed.py` — NOT invoked by the run-book
    - `code/src/data/embed_with_logging.py` — NOT invoked by the run-book
    - `code/src/data/preprocess.py` — NOT invoked by the run-book
    - `code/src/data/verify_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/embeddings.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
