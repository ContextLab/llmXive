# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw (rc=1); python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name layout_corpus  --output-dir data/raw -> rc=1
Repository Not Found for url: https://huggingface.co/api/datasets/allenai/pubmed-layout/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Primary pages (0) < 10000. Trying fallback...
Downloading repository 'allenai/pubmed-layout-fallback'...
Fallback download failed: 401 Client Error. (Request ID: Root=1-6ad11702-3a92fc9a7973394f4d5dfcf0;0d852dd0-7d67-49aa-a53d-76ff84fc726c)

Repository Not Found for url: https://huggingface.co/api/datasets/allenai/pubmed-layout-fallback/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
Total pages with layout after fallback handling: 0

❌ ERROR: Insufficient annotated pages (FR-007). Found 0, need 10000.

- python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/preprocess.py", line 18, in <module>
    import pyarrow  # ensures parquet support
    ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 17, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=1
Downloading repository 'allenai/docvqa'...
DocVQA download failed: 401 Client Error. (Request ID: Root=1-6ad11703-5d51174d7e5e86f0021a7c85;320bdf64-d59b-461d-8304-bf619eaeac3e)

Repository Not Found for url: https://huggingface.co/api/datasets/allenai/docvqa/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

❌ ERROR: 401 Client Error. (Request ID: Root=1-6ad11703-5d51174d7e5e86f0021a7c85;320bdf64-d59b-461d-8304-bf619eaeac3e)

Repository Not Found for url: https://huggingface.co/api/datasets/allenai/docvqa/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- python -m pytest -k "contract" tests/ -> rc=2
/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/tests/unit/test_preprocess.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_preprocess.py:16: in <module>
    from src.data.preprocess import preprocess_dataset
src/data/preprocess.py:18: in <module>
    import pyarrow  # ensures parquet support
../../.llmxive-venvs/PROJ-1051-llmxive-follow-up-extending-scalable-vis/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
pyarrow/lib.pyx:42: in init pyarrow.lib
    ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4
=========================== short test summary info ============================
ERROR tests/test_latent_generator.py
ERROR tests/unit/test_preprocess.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================= 1 deselected, 2 errors in 0.57s ========================



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **10537** real records with fields: questionId, question, question_types, image, docId, ucsf_document_id, ucsf_document_page_no, answers, data_split.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset, concatenate_datasets

# Load all available splits for the dataset
dataset_dict = load_dataset("lmms-lab-encoder/DocVQA", "DocVQA")
# Concatenate them into a single Dataset
combined = concatenate_datasets([split for split in dataset_dict.values()])

print(f"RECORDS={len(combined)}")
print("FIELDS=" + ",".join(combined.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
