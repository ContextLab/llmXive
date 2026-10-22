# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”
- code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”
- code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”
- code/run_quantization_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# We'll create a dummy input to the model's main bloc…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/run_router_inference.py: self-declared fabricated metric — “…entropy, matrix index, and a placeholder metric structure.…”; code/runners/router_inference_runner.py: self-declared fabricated metric — “…# For this runner, we simulate the metric collection structure.…”; code/analysis/clustering.py: synthetic/fake INPUT data not authorized by the spec — “…cluster center values to generate synthetic activations         # th…”; run-book completed but produced no data/figure artifacts; 6 declared deliverable(s) absent: data/processed/clustering_report.json; data/processed/correlation_results.json; data/processed/entropy_scores.csv

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/clustering_report.json
- data/processed/correlation_results.json
- data/processed/entropy_scores.csv
- data/processed/final_evaluation_report.json
- data/processed/logs/model_load_log.json
- data/processed/prompts.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `pycocotools` to the project's `requirements.txt` and `pip install pycocotools`.
- **Verified**: this loads **5000** real records with fields: image_id, file_name, height, width, captions.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os, urllib.request, zipfile, tempfile
from pycocotools.coco import COCO

# Download COCO 2017 validation annotations
url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
tmp_dir = tempfile.mkdtemp()
zip_path = os.path.join(tmp_dir, "ann.zip")
urllib.request.urlretrieve(url, zip_path)
with zipfile.ZipFile(zip_path, "r") as z:
    json_path = z.extract("annotations/captions_val2017.json", path=tmp_dir)

coco = COCO(json_path)
img_ids = coco.getImgIds()
records = []
for img_id in img_ids:
    img_info = coco.loadImgs(img_id)[0]
    ann_ids = coco.getAnnIds(imgIds=img_id)
    anns = coco.loadAnns(ann_ids)
    captions = " ".join(a["caption"] for a in anns)
    records.append({
        "image_id": img_info["id"],
        "file_name": img_info["file_name"],
        "height": img_info["height"],
        "width": img_info["width"],
        "captions": captions,
    })
print(f"RECORDS={len(records)}")
print("FIELDS=image_id,file_name,height,width,captions")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clustering_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/load_matrices.py` — NOT invoked by the run-book
    - `code/analysis/mse_validator.py` — NOT invoked by the run-book
    - `code/analysis/router.py` — NOT invoked by the run-book
    - `code/analysis/router_api_docs.py` — NOT invoked by the run-book
    - `code/config.py` — IS a run-book command
    - `code/main_validation.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clustering_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clustering.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/config.py` — IS a run-book command
    - `code/main_validation.py` — NOT invoked by the run-book
    - `code/run_correlation.py` — NOT invoked by the run-book
    - `code/validation/validate_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/generate_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/config.py` — IS a run-book command
    - `code/run_router_inference_modular.py` — NOT invoked by the run-book
    - `code/runners/correlation_runner.py` — NOT invoked by the run-book
    - `code/runners/router_inference_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_evaluation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistical_test.py` — NOT invoked by the run-book
    - `code/run_evaluation.py` — NOT invoked by the run-book
    - `code/run_evaluation_modular.py` — NOT invoked by the run-book
    - `code/utils/data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_evaluation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/logs/model_load_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — IS a run-book command
    - `code/models/__init__.py` — NOT invoked by the run-book
    - `code/models/flux_wan_loader.py` — NOT invoked by the run-book
    - `code/models/loader.py` — NOT invoked by the run-book
    - `code/models/model_load_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/logs/model_load_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/config.py` — IS a run-book command
    - `code/data/download_diverse_prompts.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/preprocess_coco.py` — NOT invoked by the run-book
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/evaluation/timing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
