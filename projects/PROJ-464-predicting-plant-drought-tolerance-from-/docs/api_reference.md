# API Reference

This document provides a detailed reference for the `code/` module functions used in the llmXive pipeline for predicting plant drought tolerance.

## Configuration

### `code/config.py`

**`Hyperparameters`** (Dataclass)
Configuration container for project-wide settings.
- `random_seed`: int (Default: 42)
- `vif_threshold`: float (Default: 5.0)
- `min_sample_size`: int (Default: 55)

**`ensure_directories()`**
Creates required directory structure (`data/raw`, `data/derived`, `state`, `results`, etc.) based on `config.py`.

**`get_config_summary()`**
Returns a dictionary summary of the current configuration state.

## Data Acquisition

### `code/download_images.py`

**`main()`**
Fetches root images from the NPPN Plant Phenome Pipeline (HuggingFace: `nppn/root-phenotyping`).
- **Behavior**: Downloads to `data/raw/nppn_images/`.
- **Error Handling**: Halts with `RepositoryNotFoundError` or `LocalEntryNotFoundError` if the dataset is unavailable. No synthetic fallback.

### `code/download_traits.py`

**`main()`**
Fetches physiological trait data (stomatal conductance, photosynthesis) using the `trydata` package.
- **Authentication**: Requires `TRY_API_KEY` environment variable.
- **Output**: Prepares data for merging with RSA metrics.

### `code/fetch_phylogeny.py`

**`get_species_list()`**
Retrieves the list of unique species from the RSA metrics dataset.

**`resolve_taxon_ids(species_list)`**
Maps species names to Open Tree of Life taxon IDs.

**`fetch_phylogenetic_tree(taxon_ids)`**
Fetches the phylogenetic tree from the Open Tree of Life API.
- **Output**: `data/derived/phylogenetic_tree.newick`.
- **Error Handling**: Halts immediately if the tree cannot be fetched (PGLS requirement).

**`save_tree(tree_newick, output_path)`**
Writes the Newick string to disk.

## Data Processing & Models

### `code/preprocess_images.py`

**`load_and_preprocess_image(image_path)`**
Loads an image and converts to grayscale.

**`extract_skeleton_metrics(skeleton)`**
Calculates depth and branch points from the skeletonized image.

**`calculate_branching_density(branch_points, endpoints, total_length)`**
Computes branching density: `(branch_points - endpoints) / total_length`.

**`process_directory(input_dir, output_csv)`**
Orchestrates the processing of all images in a directory and saves `data/derived/rsametrics.csv`.

### `code/merge_data.py`

**`load_rsa_metrics(csv_path)`**
Loads and validates RSA metrics.

**`load_physiological_data(merged_data)`**
Loads physiological traits and merges on species ID.

**`validate_sample_size(df)`**
Ensures merged dataset size >= 55. Halts if insufficient.

### `code/models.py`

**`RootImage`, `RSAMetrics`, `PhysioTrait`**
Pydantic models defining the schema for input data entities.

**`fit_ols(X, y)`**
Fits an Ordinary Least Squares regression. Returns coefficients and R².

**`fit_ridge(X, y, alpha)`**
Fits a Ridge regression model.

**`fit_lasso(X, y, alpha)`**
Fits a Lasso regression model.

**`fit_random_forest(X, y)`**
Fits a Random Forest Regressor (n_estimators=100).

**`fit_pgl(df, tree_path, formula)`**
Performs Phylogenetic Generalized Least Squares using `caper`.
- **Input**: Dataframe with species, tree path, and formula (e.g., "conductance ~ depth").
- **Output**: Returns PGLS statistics and lambda.

**`fit_rf_classification(X, y)`**
Fits a Random Forest Classifier for drought tolerance (High/Low) based on proxy variables.

## Analysis & Reporting

### `code/analysis.py`

**`calculate_vif(df, predictors)`**
Calculates Variance Inflation Factor for a set of predictors.

**`perform_pca(df, predictors)`**
Performs PCA to handle collinearity.

**`multiple_comparison_correction(p_values)`**
Applies Bonferroni or FDR correction to p-values.

**`detect_tolerance_proxies(merged_data)`**
Checks for independent tolerance proxies (e.g., survival rate) to enable classification.
- **Output**: Updates `state/proxy_detection.yaml`.

**`run_sensitivity_analysis(model, threshold_range)`**
Sweeps classification thresholds to evaluate robustness (Accuracy, Precision, Recall, F1, FPR, FNR).

### `code/generate_report.py`

**`check_vif_compliance(vif_results)`**
Determines if VIF > 5 and flags variables for suppression.

**`generate_framing_text(model_results, vif_status)`**
Generates the report text, explicitly suppressing independent effect claims for high-VIF variables.

**`main()`**
Orchestrates the generation of `data/derived/model_results.csv` and `data/derived/report_framing.md`.

### `code/generate_sensitivity_report.py`

**`generate_report_content(sweep_results)`**
Creates the sensitivity analysis report, including threshold justification.
