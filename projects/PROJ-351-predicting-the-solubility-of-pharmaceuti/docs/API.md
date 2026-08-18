# API Reference

This document describes the public interfaces of the core modules in the `code/` directory.

## Data Modules

### `code/data/download_esol`
- `fetch_esol_dataset()`: Downloads the ESOL dataset from the verified source.
- `save_raw_csv(df, path)`: Saves the dataframe to a CSV file.
- `verify_checksum(file_path, expected_hash)`: Validates the downloaded file integrity.
- `main()`: Entry point for the download script.

### `code/data/preprocess`
- `get_atom_features(mol)`: Extracts atom features from an RDKit molecule.
- `get_bond_features(mol)`: Extracts bond features from an RDKit molecule.
- `process_molecule(smiles)`: Converts a SMILES string to a graph dictionary.
- `load_and_preprocess(raw_path, processed_path)`: Orchestrates the preprocessing pipeline.
- `main()`: Entry point for the preprocessing script.

### `code/data/split`
- `load_cleaned_data(path)`: Loads preprocessed graph data.
- `create_stratified_splits(data, logS_col, train_ratio, val_ratio)`: Performs stratified splitting.
- `save_split_indices(splits, output_dir)`: Saves split indices to JSON.
- `main()`: Entry point for the splitting script.

## Model Modules

### `code/models/baseline_rf`
- `generate_morgan_fingerprint(mol, radius=2, n_bits=2048)`: Generates a Morgan fingerprint vector.
- `train_random_forest(X_train, y_train)`: Trains a Random Forest model.
- `evaluate_model(model, X_test, y_test)`: Calculates RMSE and R².
- `save_model(model, path)`: Saves the trained model to disk.
- `main()`: Entry point for baseline training.

### `code/models/gnn_mpnn`
- `MPNNLayer`: PyTorch Module implementing a single message passing layer.
- `GNNMPNN`: The full MPNN model class.
- `main()`: Entry point for GNN model definition (if needed for CLI).

## Training Modules

### `code/training/train_gnn`
- `load_graph_data(data_path)`: Loads processed graph data.
- `prepare_data_loaders(data, batch_size)`: Creates PyTorch DataLoaders.
- `train_model(model, train_loader, val_loader, epochs)`: Runs the training loop with early stopping.
- `save_model(model, path)`: Saves the best model checkpoint.
- `main()`: Entry point for GNN training.

## Evaluation Modules

### `code/evaluation/metrics`
- `calculate_rmse(y_true, y_pred)`: Computes Root Mean Squared Error.
- `calculate_r2(y_true, y_pred)`: Computes R-squared score.
- `evaluate_gnn_on_test_set(model, test_loader)`: Evaluates the GNN on the test set.
- `save_metrics_and_predictions(metrics, predictions, path)`: Saves results to JSON/CSV.

### `code/evaluation/statistical_test`
- `calculate_absolute_errors(y_true, y_pred)`: Computes absolute errors.
- `perform_paired_ttest(errors1, errors2)`: Performs a paired t-test.
- `calculate_post_hoc_power(effect_size, n_samples, alpha)`: Calculates statistical power.
- `run_statistical_analysis(baseline_preds, gnn_preds)`: Orchestrates the statistical analysis.

### `code/evaluation/report_generator`
- `generate_summary_table(baseline_metrics, gnn_metrics, stats)`: Creates a summary table.
- `save_report_text(report, path)`: Saves the report to a text file.
- `main()`: Entry point for report generation.

## Configuration

### `code/config/seeds`
- `set_seed(seed)`: Sets seeds for numpy, random, and torch.
- `get_seed()`: Retrieves the current seed.
- `ensure_seeded()`: Ensures all seeds are set before execution.

## Logging

### `code/setup_logging`
- `setup_logger(name, log_file)`: Configures a JSON-formatted logger.
- `log_exclusion_counts(counts)`: Logs molecule exclusion counts.
- `log_training_metrics(metrics)`: Logs training metrics.