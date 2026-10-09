# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/download_data.py --output data/raw/ (rc=1); python code/generate_descriptors.py --input data/raw/ --output data/processed/ (rc=1); python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --output data/raw/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/download_data.py", line 13, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python code/generate_descriptors.py --input data/raw/ --output data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 152, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 136, in main
    df = load_raw_materials(input_dir)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 25, in load_raw_materials
    raise FileNotFoundError(f"No parquet files found in {input_dir}")
FileNotFoundError: No parquet files found in data/raw

- python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv -> rc=1

2026-10-09 19:18:44,335 | INFO | __main__ | Starting learning curve generation with deterministic nested subsampling
2026-10-09 19:18:44,336 | ERROR | __main__ | Failed to load dataset: Feature file not found: data/processed/magpie_features.csv

- python code/fit_scaling_laws.py --input data/processed/learning_curves.csv --output data/processed/scaling_results.csv -> rc=1

2026-10-09 19:18:45 | INFO     | __main__ | Starting scaling law fitting process
2026-10-09 19:18:45 | ERROR    | __main__ | Learning curve file not found: data/processed/learning_curves.csv

- python code/analyze_physics.py --input data/processed/scaling_results.csv --output data/processed/final_analysis.csv -> rc=1

Error in physical metrics analysis: Metric definitions missing for: spatial_locality, symmetry_sensitivity. Halting as per Task T041 requirements.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/analyze_physics.py", line 592, in main
    raise RuntimeError(
RuntimeError: Metric definitions missing for: spatial_locality, symmetry_sensitivity. Halting as per Task T041 requirements.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/analyze_physics.py", line 722, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/analyze_physics.py", line 592, in main
    raise RuntimeError(
RuntimeError: Metric definitions missing for: spatial_locality, symmetry_sensitivity. Halting as per Task T041 requirements.

- python code/visualize_results.py --input data/processed/final_analysis.csv --output figures/ -> rc=1
native files...
2026-10-09 19:18:48,292 - __main__ - ERROR - Data file missing: Learning curve file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv
2026-10-09 19:18:48,292 - __main__ - ERROR - Ensure T019 (learning curves) and T020 (scaling laws) have run successfully.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 335, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 304, in main
    lc_df = load_learning_curve_data()
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 79, in load_learning_curve_data
    raise FileNotFoundError(f"Learning curve file not found: {lc_path}")
FileNotFoundError: Learning curve file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/data/processed/learning_curves.csv

- python -m pytest tests/contract/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/.venv/bin/python: No module named pytest


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `matminer` to the project's `requirements.txt` and `pip install matminer`.
- **Verified**: this loads **1181** real records with fields: material_id, formula, property_name, property_value.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from matminer.datasets import load_dataset

df = load_dataset('elastic_tensor_2015')
print(f"RECORDS={len(df)}")
# Map dataset columns to the requested field names
mapping = {
    'material_id': 'material_id',
    'composition': 'composition',
    'formula': 'formula',
    'property_name': 'elastic_anisotropy',
    'property_value': 'elastic_anisotropy',
    'property_units': None,
    'property_type': 'elastic',
    'temperature': None,
    'source': 'source'
}
present = [req for req, col in mapping.items() if col and col in df.columns]
print('FIELDS=' + ','.join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
