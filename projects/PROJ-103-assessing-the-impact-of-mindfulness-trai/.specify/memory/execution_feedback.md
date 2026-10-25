# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/utils/seeding.py: function `main` returns a bare RNG draw (line 87) — a reported value computed from no real input
- code/src/utils/seeding.py: function `dummy` returns a bare RNG draw (line 87) — a reported value computed from no real input

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/preproc_metadata.json: results file is EMPTY ({}) — the analysis produced no values
- every produced artifact is gitignored (data/processed/preproc_metadata.json, data/raw/ds000226/dataset_description.json, data/raw/ds001692/dataset_description.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/utils/seeding.py: function `main` returns a bare RNG draw (line 87) — a reported value computed from no real input; code/src/utils/seeding.py: function `dummy` returns a bare RNG draw (line 87) — a reported value computed from no real input; 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/preproc_metadata.json: results file is EMPTY ({}) — the analysis produced no values; every produced artifact is gitignored (data/processed/preproc_metadata.json, data/raw/ds000226/dataset_description.json, data/raw/ds001692/dataset_description.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 run-book script(s) missing (plan/impl path mismatch): python code/connectivity/dmn_extraction.py  --input data/processed/fmriprep_outputs  --atlas aal  --nodes PCC mPFC IPL angular_gyrus; python code/connectivity/correlation_matrix.py  --input data/processed/fmriprep_outputs  --output data/processed/connectivity_matrices; python code/connectivity/nbs_correction.py  --input data/processed/connectivity_matrices  --output data/processed/nbs_results  --permutations 10000  --primary_threshold 3.1; 3 command(s) failed: python -m pytest tests/contract/ -v (rc=4); python -m pytest tests/unit/ -v (rc=2); python -m pytest tests/integration/test_full_pipeline.py -v (rc=4)

## Failing / missing run-book commands

- python code/connectivity/dmn_extraction.py  --input data/processed/fmriprep_outputs  --atlas aal  --nodes PCC mPFC IPL angular_gyrus -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/code/connectivity/dmn_extraction.py': [Errno 2] No such file or directory

- python code/connectivity/correlation_matrix.py  --input data/processed/fmriprep_outputs  --output data/processed/connectivity_matrices -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/code/connectivity/correlation_matrix.py': [Errno 2] No such file or directory

- python code/connectivity/nbs_correction.py  --input data/processed/connectivity_matrices  --output data/processed/nbs_results  --permutations 10000  --primary_threshold 3.1 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/code/connectivity/nbs_correction.py': [Errno 2] No such file or directory

- python code/utils/power_analysis.py  --effect-size 0.5  --alpha 0.05  --power 0.80 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/code/utils/power_analysis.py': [Errno 2] No such file or directory

- python code/paper/generate_report.py  --input data/processed/meta_analysis_results  --output paper/final_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/code/paper/generate_report.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: cov-7.1.0
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/


- python -m pytest tests/unit/ -v -> rc=2
verify_variables'
=============================== warnings summary ===============================
tests/unit/test_extract_motion.py:7
  /home/runner/work/llmXive/llmXive/projects/PROJ-103-assessing-the-impact-of-mindfulness-trai/tests/unit/test_extract_motion.py:7: DeprecationWarning: 
  Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
  (to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
  but was not found to be installed on your system.
  If this would cause problems for you,
  please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
          
    import pandas as pd

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_download_datasets.py
ERROR tests/unit/test_nilearn_fallback.py
ERROR tests/unit/test_settings.py
ERROR tests/unit/test_verify_variables.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 4 errors in 1.38s =========================


- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-103-assessing-the-impact-of-mindfulness-trai/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: cov-7.1.0
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_full_pipeline.py


