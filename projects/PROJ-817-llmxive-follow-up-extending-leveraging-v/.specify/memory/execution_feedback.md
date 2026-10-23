# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: python -m spacy download en_core_web_sm (rc=1); python -m code.src.data.download (rc=1); python -m src.data.curate (rc=1); 2 declared deliverable(s) absent: data/raw/checksums_manifest.json; data/raw/prompts_sample.parquet

## Failing / missing run-book commands

- python -m spacy download en_core_web_sm -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named spacy

- python -m code.src.data.download -> rc=1

2026-10-23 09:10:14,326 ERROR __main__: HF streaming loader failed: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-23 09:10:14,326 ERROR __main__: Data collection failed: Unable to stream dataset timbrooks/instructpix2pix from Hugging Face

- python -m src.data.curate -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named src.data.curate

- python -m src.data.human_annotation -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: No module named src.data.human_annotation

- python -m src.parser.graph_builder -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.parser.graph_builder' (ModuleNotFoundError: No module named 'src.parser')

- python -m src.verifier.baseline -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.verifier.baseline' (ModuleNotFoundError: No module named 'src.verifier')

- python -m src.verifier.augmented -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.verifier.augmented' (ModuleNotFoundError: No module named 'src.verifier')

- python -m src.analysis.stats -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.analysis.stats' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.report -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-817-llmxive-follow-up-extending-leveraging-v/bin/python: Error while finding module specification for 'src.analysis.report' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest tests/contract/test_evaluation_report.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_evaluation_report.py



## Declared deliverables still missing

- data/raw/checksums_manifest.json
- data/raw/prompts_sample.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **313010** real records with fields: original_prompt, original_image, edit_prompt, edited_prompt, edited_image.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets
from datasets import Image

ds = datasets.load_dataset(
    "timbrooks/instructpix2pix-clip-filtered",
    split="train",
    streaming=True,
)

# Disable image decoding to avoid Pillow requirement
for col, feat in ds.features.items():
    if isinstance(feat, Image):
        ds = ds.cast_column(col, Image(decode=False))

total = ds.info.splits["train"].num_examples
print(f"RECORDS={total}")

sample = next(iter(ds))
print("FIELDS=" + ",".join(sample.keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/prompts_sample.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download.py` — IS a run-book command
    - `code/tests/test_download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/prompts_sample.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
