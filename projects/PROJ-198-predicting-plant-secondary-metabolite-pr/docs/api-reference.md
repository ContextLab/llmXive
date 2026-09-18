# API Reference

## Data Module

### `code/data/download.py`

#### `download_genomes(species_list, config)`
Fetches genomic assemblies for specified species.

**Parameters**:
- `species_list` (List[str]): List of species names
- `config` (Config): Configuration object

**Returns**:
- `Dict[str, Path]`: Mapping of species to downloaded file paths

**Raises**:
- `DownloadError`: If all sources fail

**Example**:
```python
from code.data.download import download_genomes
from code.config import get_config

config = get_config()
genomes = download_genomes(["Arabidopsis thaliana"], config)
```

#### `download_metabolites(species_list, config)`
Fetches metabolite abundance tables.

**Parameters**:
- `species_list` (List[str]): List of species names
- `config` (Config): Configuration object

**Returns**:
- `pd.DataFrame`: Metabolite abundance table

**Raises**:
- `DownloadError`: If all sources fail

---

### `code/data/preprocess.py`

#### `run_antiSMASH_wrapper(genome_dir, output_dir)`
Executes antiSMASH and parses JSON output.

**Parameters**:
- `genome_dir` (Path): Directory containing genome files
- `output_dir` (Path): Directory for output files

**Returns**:
- `Dict`: BGC summary dictionary

**Raises**:
- `AntiSMASHError`: If antiSMASH execution fails

#### `harmonize_metabolites(df)`
Normalizes and transforms metabolite data.

**Parameters**:
- `df` (pd.DataFrame): Raw metabolite abundance table

**Returns**:
- `pd.DataFrame`: Harmonized metabolite table

#### `map_bgc_to_metabolite(bgc_type, mapping_source='mibig')`
Maps BGC types to metabolite classes.

**Parameters**:
- `bgc_type` (str): BGC type string
- `mapping_source` (str): 'mibig' or 'pfam'

**Returns**:
- `str`: Metabolite class or 'unknown'

#### `map_bgc_to_metabolite_dataframe(df, bgc_column, mapping_source='mibig')`
Maps BGC types in a DataFrame column.

**Parameters**:
- `df` (pd.DataFrame): DataFrame with BGC column
- `bgc_column` (str): Column name containing BGC types
- `mapping_source` (str): 'mibig' or 'pfam'

**Returns**:
- `pd.DataFrame`: DataFrame with added metabolite class column

---

### `code/data/align.py`

#### `align_data(bgc_df, metabolite_df)`
Merges genomic and metabolomic data.

**Parameters**:
- `bgc_df` (pd.DataFrame): BGC matrix
- `metabolite_df` (pd.DataFrame): Metabolite matrix

**Returns**:
- `Tuple[pd.DataFrame, float]`: Aligned dataframe and success rate

#### `save_aligned_matrix(df, output_path)`
Saves aligned matrix to CSV.

**Parameters**:
- `df` (pd.DataFrame): Aligned dataframe
- `output_path` (Path): Output file path

---

## Modeling Module

### `code/modeling/phylo.py`

#### `load_phylogeny(tree_path)`
Loads phylogenetic tree from Newick file.

**Parameters**:
- `tree_path` (Path): Path to Newick file

**Returns**:
- `dendropy.Tree`: Phylogenetic tree object

**Raises**:
- `PhylogenyError`: If tree loading fails

#### `construct_covariance_matrix(tree, species_list)`
Constructs phylogenetic covariance matrix.

**Parameters**:
- `tree` (dendropy.Tree): Phylogenetic tree
- `species_list` (List[str]): List of species names

**Returns**:
- `np.ndarray`: Covariance matrix

#### `train_pgls(X, y, covariance_matrix)`
Trains Phylogenetic Generalized Least Squares model.

**Parameters**:
- `X` (np.ndarray): Feature matrix
- `y` (np.ndarray): Target vector
- `covariance_matrix` (np.ndarray): Phylogenetic covariance

**Returns**:
- `dict`: Model results including coefficients and R²

---

### `code/modeling/train.py`

#### `apply_pca(df, n_components=None)`
Applies PCA for dimensionality reduction.

**Parameters**:
- `df` (pd.DataFrame): Feature dataframe
- `n_components` (int, optional): Number of components

**Returns**:
- `pd.DataFrame`: PCA-reduced features

#### `create_stratified_split(df, phylo_tree, test_size=0.2)`
Creates phylogenetically stratified train/test split.

**Parameters**:
- `df` (pd.DataFrame): Dataframe with species
- `phylo_tree` (dendropy.Tree): Phylogenetic tree
- `test_size` (float): Proportion for test set

**Returns**:
- `Tuple[pd.DataFrame, pd.DataFrame]`: Train and test splits

#### `train_models_loo(X, y, models)`
Trains models with Leave-One-Out cross-validation.

**Parameters**:
- `X` (np.ndarray): Feature matrix
- `y` (np.ndarray): Target vector
- `models` (Dict): Dictionary of model instances

**Returns**:
- `Dict`: Cross-validation results

#### `train_models_5fold(X, y, models, n_folds=5)`
Trains models with 5-fold cross-validation.

**Parameters**:
- `X` (np.ndarray): Feature matrix
- `y` (np.ndarray): Target vector
- `models` (Dict): Dictionary of model instances
- `n_folds` (int): Number of folds

**Returns**:
- `Dict`: Cross-validation results

---

### `code/modeling/eval.py`

#### `evaluate_models(model_results, test_data)`
Evaluates model performance on test data.

**Parameters**:
- `model_results` (Dict): Model prediction results
- `test_data` (pd.DataFrame): Test dataset

**Returns**:
- `Dict`: Evaluation metrics (R², correlation, etc.)

#### `run_phylogenetic_permutation(X, y, covariance_matrix, n_permutations=100)`
Runs phylogenetic permutation baseline.

**Parameters**:
- `X` (np.ndarray): Feature matrix
- `y` (np.ndarray): Target vector
- `covariance_matrix` (np.ndarray): Phylogenetic covariance
- `n_permutations` (int): Number of permutations

**Returns**:
- `float`: Baseline R²

#### `calculate_significance(model_r2, baseline_r2, n_permutations)`
Calculates statistical significance of model improvement.

**Parameters**:
- `model_r2` (float): Model R² score
- `baseline_r2` (float): Baseline R² score
- `n_permutations` (int): Number of permutations

**Returns**:
- `float`: p-value

#### `run_sensitivity_sweep(X, y, thresholds, models)`
Runs sensitivity analysis across BGC thresholds.

**Parameters**:
- `X` (np.ndarray): Feature matrix
- `y` (np.ndarray): Target vector
- `thresholds` (List[float]): BGC thresholds to test
- `models` (Dict): Dictionary of model instances

**Returns**:
- `Dict`: Sensitivity results per threshold

#### `calculate_variation(sensitivity_results)`
Calculates max R² variation across thresholds.

**Parameters**:
- `sensitivity_results` (Dict): Results from sensitivity sweep

**Returns**:
- `float`: Maximum R² difference

---

## Configuration Module

### `code/config.py`

#### `load_config(config_path)`
Loads configuration from YAML file.

**Parameters**:
- `config_path` (str): Path to config file

**Returns**:
- `Config`: Configuration object

#### `get_config()`
Retrieves current configuration.

**Returns**:
- `Config`: Current configuration

#### `get_species_list()`
Gets list of species from configuration.

**Returns**:
- `List[str]`: Species names

---

## Utility Modules

### `code/utils/anti_smash_parser.py`

#### `parse_anti_smash_json(json_path)`
Parses antiSMASH JSON output.

**Parameters**:
- `json_path` (str): Path to JSON file

**Returns**:
- `Dict`: Parsed BGC information

### `code/utils/report.py`

#### `generate_report(metrics, sensitivity_results, output_path)`
Generates final Markdown report.

**Parameters**:
- `metrics` (Dict): Model metrics
- `sensitivity_results` (Dict): Sensitivity analysis results
- `output_path` (str): Output file path

**Returns**:
- `Path`: Path to generated report