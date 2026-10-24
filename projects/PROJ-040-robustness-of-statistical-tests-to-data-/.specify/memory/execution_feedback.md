# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/har.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/har.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/viz/plot_results.py; 6 command(s) failed: python code/validation/validate_citations.py (rc=1); python code/data/download_datasets.py (rc=1); python code/validation/checksum_artifacts.py (rc=1)

## Failing / missing run-book commands

- python code/validation/validate_citations.py -> rc=1
Starting citation validation...
ERROR: plan.md not found at /home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/plan.md


- python code/data/download_datasets.py -> rc=1
ta
❌ Wine download failed: Failed to process Wine dataset: 13 columns passed, passed data had 14 columns
Downloading UCI Human Activity Recognition dataset...
URL: https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip
✅ HAR: All 562 columns validated as numeric.
✅ Saved to: /home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/raw/har.csv
   Shape: (7352, 562)
   Columns: 562 features + 1 label

📊 Download Summary:
  ❌ wine: None
  ✅ har: /home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/raw/har.csv

/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data/download_datasets.py:8: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd

- python code/validation/checksum_artifacts.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/validation/checksum_artifacts.py", line 13, in <module>
    from .validate_citations import compute_sha256, write_state_file
ImportError: attempted relative import with no known parent package

- python code/data/generate_contamination.py -> rc=1
mination.py:4: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data/generate_contamination.py", line 242, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data/generate_contamination.py", line 215, in main
    download_wine(str(raw_dir))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data/download_datasets.py", line 63, in download_wine
    output_path = output_dir / DATASETS["wine"]["output_file"]
                  ~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TypeError: unsupported operand type(s) for /: 'str' and 'str'

- python code/data/run_simulation.py -> rc=1
Loading sensitivity data...
Error: Sensitivity data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/processed/sensitivity.csv
Please ensure T014 (sensitivity analysis) has been run first.

/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data/run_simulation.py:4: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd

- python code/validation/checksum_artifacts.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/validation/checksum_artifacts.py", line 13, in <module>
    from .validate_citations import compute_sha256, write_state_file
ImportError: attempted relative import with no known parent package

- python code/viz/plot_results.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-040-robustness-of-statistical-tests-to-data-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/viz/plot_results.py': [Errno 2] No such file or directory


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scikit-learn` to the project's `requirements.txt` and `pip install scikit-learn`.
- **Verified**: this loads **150** real records with fields: sample_id, sepal length (cm), sepal width (cm), petal length (cm), petal width (cm), target.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import numpy as np
from sklearn.datasets import load_iris, load_wine, load_breast_cancer

def load_and_report(loader, name):
    data = loader()
    n_records = data.data.shape[0]
    fields = ["sample_id"] + list(data.feature_names) + ["target"]
    print(f"RECORDS={n_records}")
    print("FIELDS=" + ",".join(fields))

# Example: Iris dataset
load_and_report(load_iris, "iris")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
