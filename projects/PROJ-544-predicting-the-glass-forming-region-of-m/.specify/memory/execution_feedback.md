# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…/usr/bin/env python3 """ Generate synthetic alloy data for glass-for…”
- scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…nthetic_alloys():     """Generate synthetic alloy data with balanced…”
- scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…), exist_ok=True)      # Generate synthetic data     df = generate_s…”
- scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…nt(f"Generated {len(df)} synthetic alloy samples")     print(f"Output sav…”
- scripts/sample_dataset.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Using synthetic dataset: {synthetic_path}")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…/usr/bin/env python3 """ Generate synthetic alloy data for glass-for…”; scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…nthetic_alloys():     """Generate synthetic alloy data with balanced…”; scripts/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…), exist_ok=True)      # Generate synthetic data     df = generate_s…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/scripts/checksum_data.py --input data/raw/your_dataset.csv; python code/scripts/download_and_verify.py   # fetches verified datasets (when URLs are added); bash ./code/scripts/run-ci.sh; 14 command(s) failed: python scripts/generate_synthetic_data.py --output data/raw/synthetic_alloys.csv --n_samples 1000 (rc=1); python scripts/sample_dataset.py --max_ram_gb 7 --input data/raw/your_dataset.csv --output data/samples/sample.csv (rc=1); python scripts/filter_labels.py --input data/samples/sample.csv --output data/raw/filtered_alloys.csv (rc=1); 7 declared deliverable(s) absent: data/derived/descriptor_vector_vif_filtered.csv; data/derived/filtered_alloys.csv; data/derived/imbalance_report.json

## Failing / missing run-book commands

- python scripts/generate_synthetic_data.py --output data/raw/synthetic_alloys.csv --n_samples 1000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/scripts/generate_synthetic_data.py", line 15, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

- python code/scripts/checksum_data.py --input data/raw/your_dataset.csv -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/scripts/checksum_data.py': [Errno 2] No such file or directory

- python code/scripts/download_and_verify.py   # fetches verified datasets (when URLs are added) -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/scripts/download_and_verify.py': [Errno 2] No such file or directory

- python scripts/sample_dataset.py --max_ram_gb 7 --input data/raw/your_dataset.csv --output data/samples/sample.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/scripts/sample_dataset.py", line 16, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

- python scripts/filter_labels.py --input data/samples/sample.csv --output data/raw/filtered_alloys.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/scripts/filter_labels.py", line 17, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

- python code/descriptors/compute.py  --input data/raw/filtered_alloys.csv  --output data/derived/descriptors.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/descriptors/compute.py", line 10, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

- python code/descriptors/check_imbalance.py  --input data/derived/descriptors.csv  --output data/derived/imbalance_report.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/descriptors/check_imbalance.py", line 16, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

- python code/descriptors/vif_filter.py  --input data/derived/descriptors.csv  --output data/derived/descriptors_vif_filtered.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/descriptors/vif_filter.py", line 18, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

- python code/models/train.py  --input data/derived/descriptors_vif_filtered.csv  --output models/trained_models.pkl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/models/train.py", line 18, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

- python code/models/evaluate.py  --model models/trained_models.pkl  --input data/derived/descriptors_vif_filtered.csv  --output results/performance_metrics.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/models/evaluate.py", line 17, in <module>
    import joblib
ModuleNotFoundError: No module named 'joblib'

- python code/models/importance.py  --model models/trained_models.pkl  --input data/derived/descriptors_vif_filtered.csv  --output results/shap_plots/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/code/models/importance.py", line 19, in <module>
    import joblib
ModuleNotFoundError: No module named 'joblib'

- python scripts/sensitivity_analysis.py --model models/trained_models.pkl --delta_values 0.01 0.05 0.1 --output results/sensitivity_report.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/scripts/sensitivity_analysis.py", line 21, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

- python scripts/reproducibility_check.py --pipeline_dir . --runs 3 --output results/reproducibility_summary.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/scripts/reproducibility_check.py", line 21, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

- python -m pytest tests/contract/ -> rc=2
y-1.6.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 2 items / 1 error / 1 skipped

==================================== ERRORS ====================================
_ ERROR collecting projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/contract/test_shap_schema.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/contract/test_shap_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/contract/test_shap_schema.py:13: in <module>
    import numpy as np
E   ModuleNotFoundError: No module named 'numpy'
=========================== short test summary info ============================
ERROR tests/contract/test_shap_schema.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 skipped, 1 error in 0.31s ==========================


- python -m pytest tests/integration/ -> rc=2
_sampling_pipeline.py:11: in <module>
    import pandas as pd
E   ModuleNotFoundError: No module named 'pandas'
_ ERROR collecting projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/integration/test_training_pipeline.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/integration/test_training_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_training_pipeline.py:15: in <module>
    import pandas as pd
E   ModuleNotFoundError: No module named 'pandas'
=========================== short test summary info ============================
ERROR tests/integration/test_sampling_pipeline.py
ERROR tests/integration/test_training_pipeline.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.27s ===============================


- python -m pytest tests/unit/ -> rc=2
y:8: in <module>
    import pandas as pd
E   ModuleNotFoundError: No module named 'pandas'
_ ERROR collecting projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/unit/test_vif_filter.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-544-predicting-the-glass-forming-region-of-m/tests/unit/test_vif_filter.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_vif_filter.py:10: in <module>
    import numpy as np
E   ModuleNotFoundError: No module named 'numpy'
=========================== short test summary info ============================
ERROR tests/unit/test_compute_descriptors.py
ERROR tests/unit/test_reproducibility.py
ERROR tests/unit/test_validate_elements.py
ERROR tests/unit/test_vif_filter.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 0.34s ===============================


- bash ./code/scripts/run-ci.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/derived/descriptor_vector_vif_filtered.csv
- data/derived/filtered_alloys.csv
- data/derived/imbalance_report.json
- data/derived/invalid_elements.csv
- data/derived/pca_components.csv
- data/derived/valid_elements.csv
- data/derived/vif_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/descriptor_vector_vif_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/vif_filter.py` — IS a run-book command
    - `code/models/importance.py` — IS a run-book command
    - `scripts/reproducibility_check.py` — IS a run-book command
    - `scripts/sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/descriptor_vector_vif_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/filtered_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/evaluate.py` — IS a run-book command
    - `code/models/train.py` — IS a run-book command
    - `scripts/filter_labels.py` — IS a run-book command
    - `scripts/reproducibility_check.py` — IS a run-book command
    - `scripts/sample_dataset.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/filtered_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/imbalance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/check_imbalance.py` — IS a run-book command
    - `scripts/reproducibility_check.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/imbalance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/invalid_elements.csv` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/validate_elements.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/invalid_elements.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/pca_components.csv` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/vif_filter.py` — IS a run-book command
    - `scripts/reproducibility_check.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/pca_components.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/valid_elements.csv` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/validate_elements.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/valid_elements.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/vif_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors/vif_filter.py` — IS a run-book command
    - `code/descriptors/vif_report.py` — NOT invoked by the run-book
    - `scripts/reproducibility_check.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/vif_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
