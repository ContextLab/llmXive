# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 run-book script(s) missing (plan/impl path mismatch): python code/data/preprocess.py  --input data/raw/qm9.parquet  --output data/processed/graphs.pt; python code/data/split.py  --graphs data/processed/graphs.pt  --train-ratio 0.80 --val-ratio 0.10 --test-ratio 0.10  --strategy scaffold; python code/data/validate_proxy.py  --qm9 data/processed/graphs.pt  --nist-url https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt  --sample-size 500; 1 command(s) failed: python code/data/download.py (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
gface.co/deepchem/qm9/resolve/main/dataset_infos.json.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/download.py", line 96, in <module>
    download_and_verify()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/download.py", line 58, in download_and_verify
    column_names = _load_dataset_schema(DATASET_NAME)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/download.py", line 27, in _load_dataset_schema
    raise RuntimeError("Could not retrieve QM9 schema information") from exc
RuntimeError: Could not retrieve QM9 schema information

- python code/data/preprocess.py  --input data/raw/qm9.parquet  --output data/processed/graphs.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/preprocess.py': [Errno 2] No such file or directory

- python code/data/split.py  --graphs data/processed/graphs.pt  --train-ratio 0.80 --val-ratio 0.10 --test-ratio 0.10  --strategy scaffold -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/split.py': [Errno 2] No such file or directory

- python code/data/validate_proxy.py  --qm9 data/processed/graphs.pt  --nist-url https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt  --sample-size 500 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/data/validate_proxy.py': [Errno 2] No such file or directory

- python code/experiments/train.py  --config code/utils/config.yaml  --batch-size 64  --max-epochs 200  --timeout-hours 6 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/train.py': [Errno 2] No such file or directory

- python code/models/baselines.py --type lr -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/models/baselines.py': [Errno 2] No such file or directory

- python code/models/baselines.py --type dftb -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/models/baselines.py': [Errno 2] No such file or directory

- python code/experiments/ablation.py  --feature bond_type  --perturbation zero  --num-runs 3  --subset-size <sufficiently large subset>  --batch-size 64  --max-epochs 100  --bootstrap-samples a sufficiently large number of samples  --runtime-guard-hours 4 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/ablation.py': [Errno 2] No such file or directory

- python code/experiments/ablation.py  --feature bond_type  --perturbation zero  --num-runs 3  --subset-size 10000  --batch-size 64  --max-epochs 100  --bootstrap-samples 1000  --runtime-guard-hours 4  --resume-from results/ablation_part1.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/ablation.py': [Errno 2] No such file or directory

- python code/experiments/evaluate.py  --model-path code/models/best_model.pth  --test-set data/splits/test.pt  --output-dir results/  --ig-sample-size sufficiently large -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-268-predicting-molecular-ionization-energies/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-268-predicting-molecular-ionization-energies/code/experiments/evaluate.py': [Errno 2] No such file or directory


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `qm9pack` to the project's `requirements.txt` and `pip install qm9pack`.
- **Verified**: this loads **130831** real records with fields: XYZ_file, Index, SMILES, InChi, N_atoms, Stoichiometry, Elements, XYZ_Ang, Mulliken_pop, Harmonic_Freq_cmi, RotA_GHz, RotB_GHz, RotC_GHz, Dipole_debye, Polarizability_bohr3, HOMO_au, LUMO_au, HOMO_LUMO_gap_au, R2_bohr2, ZPVE_au, InternalEnergy_0K_au, InternalEnergy_298K_au, Enthalphy_298K_au, GibbsFreeEnergy_298K_au, Heatcapacity_Cv_cal_mol_K, A_xx, A_xy, A_yy, A_xz, A_yz, A_zz.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import qm9pack

records = qm9pack.get_data('qm9')

print(f"RECORDS={len(records)}")
if not records.empty:
    print("FIELDS=" + ",".join(records.columns.tolist()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
