# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/extraction.py: function `extract_roi_timeseries` returns a bare RNG draw (line 42) — a reported value computed from no real input
- code/src/preprocessing.py: function `perform_nuisance_regression` returns a bare RNG draw (line 45) — a reported value computed from no real input

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/subject_qc_list.json: results file is EMPTY ([]) — the analysis produced no values
- data/processed/subjects_metadata.json: results file is EMPTY ([]) — the analysis produced no values
- every produced artifact is gitignored (data/processed/subject_qc_list.json, data/processed/subjects_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/main.py --step download_qc &&  python code/src/main.py --step extract_connectivity &&  python code/src/main.py --step stats_viz --seed 42`
  - script usage: `main.py [-h] [--step STEP_FLAG] [--seed SEED] [step_pos]`
  - argparse error: `main.py: error: unrecognized arguments: python code/src/main.py && python code/src/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/extraction.py: function `extract_roi_timeseries` returns a bare RNG draw (line 42) — a reported value computed from no real input; code/src/preprocessing.py: function `perform_nuisance_regression` returns a bare RNG draw (line 45) — a reported value computed from no real input; 2 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/subject_qc_list.json: results file is EMPTY ([]) — the analysis produced no values; data/processed/subjects_metadata.json: results file is EMPTY ([]) — the analysis produced no values; every produced artifact is gitignored (data/processed/subject_qc_list.json, data/processed/subjects_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/src/main.py --step download_qc (rc=1); python code/src/main.py --step download_qc &&  python code/src/main.py --step extract_connectivity &&  python code/src/main.py --step stats_viz --seed 42 (rc=2); python -m pytest code/tests/ -v (rc=2); 1 declared deliverable(s) absent: data/results/sensitivity_curve.csv

## Failing / missing run-book commands

- python code/src/main.py --step download_qc -> rc=1
nt subjects (N=0) for valid permutation test.
2026-10-21 04:39:32,635 - __main__ - ERROR - Pipeline step failed
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-474-neural-correlates-of-simulated-social-ex/code/src/main.py", line 125, in main
    run_download_qc_step()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-474-neural-correlates-of-simulated-social-ex/code/src/main.py", line 34, in run_download_qc_step
    run_qc_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-474-neural-correlates-of-simulated-social-ex/code/src/qc.py", line 313, in main
    run_qc_pipeline(raw_dir, output_dir, motion_threshold=motion_threshold)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-474-neural-correlates-of-simulated-social-ex/code/src/qc.py", line 299, in run_qc_pipeline
    check_subject_count(filtered_subjects, min_count=10)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-474-neural-correlates-of-simulated-social-ex/code/src/qc.py", line 257, in check_subject_count
    raise InsufficientSubjectsError(retained_count)
src.exceptions.InsufficientSubjectsError: Insufficient subjects (N=0) for valid permutation test.

- python code/src/main.py --step download_qc &&  python code/src/main.py --step extract_connectivity &&  python code/src/main.py --step stats_viz --seed 42 -> rc=2

usage: main.py [-h] [--step STEP_FLAG] [--seed SEED] [step_pos]
main.py: error: unrecognized arguments: python code/src/main.py && python code/src/main.py

- python -m pytest code/tests/ -v -> rc=2
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
code/tests/unit/test_utils.py:4: in <module>
    from src.utils import log_exception
E   ModuleNotFoundError: No module named 'src.utils'
=========================== short test summary info ============================
ERROR code/tests/test_qc.py
ERROR code/tests/unit/test_data_loader.py
ERROR code/tests/unit/test_integrity.py
ERROR code/tests/unit/test_preprocessing.py
ERROR code/tests/unit/test_stats.py
ERROR code/tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.70s ===============================



## Declared deliverables still missing

- data/results/sensitivity_curve.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `nilearn` to the project's `requirements.txt` and `pip install nilearn`.
- **Verified**: this loads **49** real records with fields: Background, Frontal Pole, Insular Cortex, Superior Frontal Gyrus, Middle Frontal Gyrus, Inferior Frontal Gyrus, pars triangularis, Inferior Frontal Gyrus, pars opercularis, Precentral Gyrus, Temporal Pole, Superior Temporal Gyrus, anterior division, Superior Temporal Gyrus, posterior division, Middle Temporal Gyrus, anterior division, Middle Temporal Gyrus, posterior division, Middle Temporal Gyrus, temporooccipital part, Inferior Temporal Gyrus, anterior division, Inferior Temporal Gyrus, posterior division, Inferior Temporal Gyrus, temporooccipital part, Postcentral Gyrus, Superior Parietal Lobule, Supramarginal Gyrus, anterior division, Supramarginal Gyrus, posterior division, Angular Gyrus, Lateral Occipital Cortex, superior division, Lateral Occipital Cortex, inferior division, Intracalcarine Cortex, Frontal Medial Cortex, Juxtapositional Lobule Cortex (formerly Supplementary Motor Cortex), Subcallosal Cortex, Paracingulate Gyrus, Cingulate Gyrus, anterior division, Cingulate Gyrus, posterior division, Precuneous Cortex, Cuneal Cortex, Frontal Orbital Cortex, Parahippocampal Gyrus, anterior division, Parahippocampal Gyrus, posterior division, Lingual Gyrus, Temporal Fusiform Cortex, anterior division, Temporal Fusiform Cortex, posterior division, Temporal Occipital Fusiform Cortex, Occipital Fusiform Gyrus, Frontal Opercular Cortex, Central Opercular Cortex, Parietal Opercular Cortex, Planum Polare, Heschl's Gyrus (includes H1 and H2), Planum Temporale, Supracalcarine Cortex, Occipital Pole.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from nilearn import datasets
atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
labels = atlas.labels
print(f'RECORDS={len(labels)}')
print('FIELDS=' + ','.join(labels))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/sensitivity_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats.py` — NOT invoked by the run-book
    - `code/tests/unit/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
