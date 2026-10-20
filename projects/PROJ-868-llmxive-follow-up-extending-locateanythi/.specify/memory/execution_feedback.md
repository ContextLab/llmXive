# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ (rc=1); python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true (rc=1); python -m pytest -q tests/contract/ (rc=4)

## Failing / missing run-book commands

- python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src')

- python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pycocotools` to the project's `requirements.txt` and `pip install pycocotools`.
- **Verified**: this loads **36781** real records with fields: segmentation, area, iscrowd, image_id, bbox, category_id, id.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os, ssl, urllib.request, zipfile
from pycocotools.coco import COCO

ZIP_URL = "https://images.cocodataset.org/annotations/annotations_trainval2017.zip"
ZIP_PATH = "/tmp/annotations_trainval2017.zip"
JSON_NAME = "annotations/instances_val2017.json"
JSON_PATH = "/tmp/instances_val2017.json"

if not os.path.exists(ZIP_PATH):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(ZIP_URL, context=ctx) as resp, open(ZIP_PATH, "wb") as out:
        out.write(resp.read())

if not os.path.exists(JSON_PATH):
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        with zf.open(JSON_NAME) as src, open(JSON_PATH, "wb") as dst:
            dst.write(src.read())

coco = COCO(JSON_PATH)

records = len(coco.anns)
print(f"RECORDS={records}")

if records:
    sample_ann = next(iter(coco.anns.values()))
    fields = ",".join(sample_ann.keys())
    print(f"FIELDS={fields}")
else:
    raise RuntimeError("No annotation records loaded")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
