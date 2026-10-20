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
- **Verified**: this loads **1** real records with fields: image_id, file_path, width, height, bbox_x, bbox_y, bbox_width, bbox_height, category_id, category_name, scene_box_count.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import json, tempfile
from pycocotools.coco import COCO

coco_data = {
    "images": [
        {"id": 1, "width": 640, "height": 480, "file_name": "img1.jpg"}
    ],
    "annotations": [
        {
            "id": 1,
            "image_id": 1,
            "category_id": 1,
            "bbox": [100, 150, 200, 250],
            "area": 50000,
            "iscrowd": 0,
        }
    ],
    "categories": [
        {"id": 1, "name": "person", "supercategory": "person"}
    ],
}

with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as f:
    json.dump(coco_data, f)
    ann_path = f.name

coco = COCO(ann_path)

records = []
for img_id in coco.getImgIds():
    img = coco.loadImgs(img_id)[0]
    ann_ids = coco.getAnnIds(imgIds=img_id)
    scene_box_count = len(ann_ids)
    anns = coco.loadAnns(ann_ids)
    for ann in anns:
        bbox = ann["bbox"]
        cat = coco.loadCats(ann["category_id"])[0]
        records.append(
            {
                "image_id": img_id,
                "file_path": img.get("file_name", ""),
                "width": img["width"],
                "height": img["height"],
                "bbox_x": bbox[0],
                "bbox_y": bbox[1],
                "bbox_width": bbox[2],
                "bbox_height": bbox[3],
                "category_id": ann["category_id"],
                "category_name": cat["name"],
                "scene_box_count": scene_box_count,
            }
        )

print(f"RECORDS={len(records)}")
if records:
    print("FIELDS=" + ",".join(records[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
