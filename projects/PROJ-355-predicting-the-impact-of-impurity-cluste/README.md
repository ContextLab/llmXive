# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Execution
python -m code.main

## Data Provenance
The bulk alloy records are sourced from the Open Quantum Materials Database (OQMD) using the verified OQMD loader (`datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`). Materials‑Project waiver is documented in the project plan because {{claim:c_31906f57}} (Wikidata Q105085929, https://www.wikidata.org/wiki/Q105085929) All raw data reside under the `data/raw/` directory.

## Research Question
How does impurity clustering in the bulk lattice affect the thermodynamic driving force for segregation to grain boundaries?
