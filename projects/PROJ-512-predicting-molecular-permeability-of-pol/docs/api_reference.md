# API Reference

## `code/data/ingestion.py`
- `fetch_nist_pubchem_data()`: Fetches raw data from NIST.
- `smiles_to_polymer_graph(smiles)`: Converts SMILES to `PolymerGraph`.
- `calculate_mw(mol)`: Calculates molecular weight.
- `clean_data(df)`: Filters missing values and duplicates.

## `code/data/preprocessing.py`
- `extract_graph_features(pgraph)`: Extracts 2D node/edge features.
- `murcko_scaffold_split(df)`: Splits data by unique scaffolds.
- `save_split_indices(splits, path)`: Saves split JSON.

## `code/models/gnn.py`
- `PolymerGNN`: The main GNN model class.
- `polymer_graph_to_pyg_data(pgraph)`: Converts to PyTorch Geometric Data.

## `code/models/baselines.py`
- `RandomForestBaseline`: Uses ECFP4 fingerprints.
- `LinearRegressionBaseline`: Uses RDKit descriptors.
- `RandomizedTopologyControlBaseline`: Randomized edge control.

## `code/evaluation/stats.py`
- `wilcoxon_signed_rank_test(model_a, model_b)`: Statistical comparison.
- `calculate_vif(descriptors)`: Variance Inflation Factor.
- `sensitivity_analysis_sweep(metrics)`: Threshold sweep analysis.
