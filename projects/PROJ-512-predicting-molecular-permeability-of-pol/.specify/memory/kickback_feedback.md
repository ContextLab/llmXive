# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): The provided `simulation.py` contains a partial implementation that stops before generating SMILES strings and never writes any data to a CSV file. Moreover, the required output file `projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/simulation_data.csv` is missing entirely. The task’s core requirement—producing and saving a synthetic dataset—has not been fulfilled.
- `T020` (rejected 1x): The `preprocessing.py` file does not contain any implementation of Murcko scaffold extraction or splitting (it ends abruptly with a broken return statement and no use of RDKit). Moreover, the required output file `code/data/processed/scaffold_split_indices.json` is missing. The task’s core functionality and its resulting artifact are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

