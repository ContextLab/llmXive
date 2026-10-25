# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Execution
python -m code.main

## Data Provenance
The bulk alloy records are sourced from the Open Quantum Materials Database (OQMD) using the HuggingFace `datasets` loader (`datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`). Materials Project data are omitted due to a documented waiver (no unauthenticated open source available). [UNRESOLVED-CLAIM: c_6892edd7 — status=not_enough_info] All raw data files are stored under the `data/raw/` directory. [UNRESOLVED-CLAIM: c_40e39f03 — status=not_enough_info]

## Research Question
How does impurity clustering in the bulk lattice affect the thermodynamic driving force for segregation to grain boundaries?