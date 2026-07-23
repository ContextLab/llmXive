# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/explainability.py: self-declared fabricated metric — “…ive.")             # Create a dummy result if no data             result…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/explainability.py: self-declared fabricated metric — “…ive.")             # Create a dummy result if no data             result…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/data/fingerprint.py; python code/models/rf.py; 5 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/models/baseline.py (rc=1); 5 declared deliverable(s) absent: data/derived/baseline_test_predictions.csv; data/derived/data_quality_report.csv; data/derived/model_comparison.png

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/data/download.py", line 20, in <module>
    from utils.config import MAX_DEPTH  # Importing config constants if needed later
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'MAX_DEPTH' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/utils/config.py)
- python code/data/preprocess.py -> rc=1
    2026-07-23 01:39:41,946 - __main__ - ERROR - Input file data/raw/chembl_dataset.csv not found. Please run T008 first.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/data/preprocess.py", line 349, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/data/preprocess.py", line 296, in main
    raise FileNotFoundError(f"Input file {input_file} not found.")
FileNotFoundError: Input file data/raw/chembl_dataset.csv not found.
- python code/data/fingerprint.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/data/fingerprint.py': [Errno 2] No such file or directory
- python code/models/baseline.py -> rc=1
    INFO:__main__:Starting baseline prediction computation...
ERROR:root:File not found: data/derived/train_set.csv
ERROR:__main__:Data processing failed.
- python code/models/rf.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/models/rf.py': [Errno 2] No such file or directory
- python code/analysis/stats.py -> rc=1
    erties-from-ope/data/derived/baseline_test_predictions.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/stats.py", line 356, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/stats.py", line 332, in main
    results = run_statistical_comparison()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/stats.py", line 148, in run_statistical_comparison
    baseline_df = load_baseline_predictions(baseline_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/stats.py", line 37, in load_baseline_predictions
    raise FileNotFoundError(f"Baseline predictions file not found: {path}")
FileNotFoundError: Baseline predictions file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/baseline_test_predictions.csv
- python code/analysis/explainability.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 101, in <module>
    def calculate_shap_interactions(model: Any, X: np.ndarray, feature_names: List[str] = None) -> shap.InteractionValues:
                                                                                                   ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'shap' has no attribute 'InteractionValues'

## Declared deliverables still missing

- data/derived/baseline_test_predictions.csv
- data/derived/data_quality_report.csv
- data/derived/model_comparison.png
- data/derived/rf_test_predictions.csv
- data/derived/train_set.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PubChemPy` to the project's `requirements.txt` and `pip install PubChemPy`.
- **Verified**: this loads **5** real records with fields: LogP, Molecular Weight, SMILES.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp
cids = [2244, 3672, 5957, 702, 5281]
props = ['IsomericSMILES','XLogP','WaterSolubility','BoilingPoint','MolecularWeight','RecordType']
compounds = pcp.get_compounds(cids, properties=props)
records = []
for c in compounds:
    rec = {}
    if getattr(c, 'isomeric_smiles', None): rec['SMILES'] = c.isomeric_smiles
    if getattr(c, 'xlogp', None) is not None: rec['LogP'] = c.xlogp
    if getattr(c, 'water_solubility', None) is not None: rec['Solubility'] = c.water_solubility
    if getattr(c, 'boiling_point', None) is not None: rec['Boiling Point'] = c.boiling_point
    if getattr(c, 'molecular_weight', None) is not None: rec['Molecular Weight'] = c.molecular_weight
    if getattr(c, 'record_type', None) is not None: rec['Property Type'] = c.record_type
    if rec:
        records.append(rec)
print(f"RECORDS={len(records)}")
if records:
    fields = set()
    for r in records:
        fields.update(r.keys())
    print("FIELDS=" + ",".join(sorted(fields)))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/baseline_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/baseline_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/data_quality_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/data_quality_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/model_comparison.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/model_comparison.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rf_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/rf_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline.py` — IS a run-book command
    - `code/models/random_forest.py` — NOT invoked by the run-book
    - `code/data/fingerprints.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/derived/train_set.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/baseline.py`, `code/models/random_forest.py`, `code/data/fingerprints.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/train_set.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/baseline.py`, `code/models/random_forest.py`, `code/data/fingerprints.py`.

### `data/raw/chembl_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/chembl_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/preprocess.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/baseline_test_predictions.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/stats.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/baseline_test_predictions.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/stats.py`.
