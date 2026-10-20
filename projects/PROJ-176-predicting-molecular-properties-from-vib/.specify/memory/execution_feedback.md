# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…str, np.ndarray]:     """Generate synthetic noise for domain shift s…”
- code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic validation data (Domain Shift Simulation…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…str, np.ndarray]:     """Generate synthetic noise for domain shift s…”; code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic validation data (Domain Shift Simulation…”; 8 command(s) failed: python code/main.py download (rc=1); python code/main.py preprocess (rc=1); python code/main.py train --max-samples 30000 (rc=1); 4 declared deliverable(s) absent: data/processed/aligned_dataset.npz; data/processed/alignment_report.json; data/raw/ir_spectra.parquet

## Failing / missing run-book commands

- python code/main.py download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/main.py preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/main.py train --max-samples 30000 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/main.py evaluate --checkpoint models/checkpoint_best.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/main.py validate --checkpoint models/checkpoint_best.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/main.py control --checkpoint models/checkpoint_best.pt -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/main.py", line 14, in <module>
    from utils.seed_utils import set_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/utils/seed_utils.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python -m pytest tests/ -v > logs/pytest.log 2>&1 -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-176-predicting-molecular-properties-from-vib/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: >


- python -m pytest tests/ -v > logs/pytest.log 2>&1 -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-176-predicting-molecular-properties-from-vib/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.01s =============================

ERROR: file or directory not found: >



## Declared deliverables still missing

- data/processed/aligned_dataset.npz
- data/processed/alignment_report.json
- data/raw/ir_spectra.parquet
- data/raw/qm9.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `qm9pack` to the project's `requirements.txt` and `pip install qm9pack`.
- **Verified**: this loads **130831** real records with fields: XYZ_file, Index, SMILES, InChi, N_atoms, Stoichiometry, Elements, XYZ_Ang, Mulliken_pop, Harmonic_Freq_cmi, RotA_GHz, RotB_GHz, RotC_GHz, Dipole_debye, Polarizability_bohr3, HOMO_au, LUMO_au, HOMO_LUMO_gap_au, R2_bohr2, ZPVE_au, InternalEnergy_0K_au, InternalEnergy_298K_au, Enthalphy_298K_au, GibbsFreeEnergy_298K_au, Heatcapacity_Cv_cal_mol_K, A_xx, A_xy, A_yy, A_xz, A_yz, A_zz.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import qm9pack
import pandas as pd

# Load the full QM9 dataset (the required argument is the dataset name)
data = qm9pack.get_data('qm9')

if isinstance(data, pd.DataFrame):
    count = len(data)
    fields = list(data.columns)
else:
    count = len(data)
    fields = list(data[0].keys()) if count else []

print(f"RECORDS={count}")
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_dataset.npz` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alignment_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ir_spectra.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/scripts/profile_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ir_spectra.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/qm9.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/scripts/profile_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/qm9.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
