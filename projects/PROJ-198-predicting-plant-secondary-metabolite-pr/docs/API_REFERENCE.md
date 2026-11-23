# API Reference

## `code.config`

- `load_config(path: str) -> Config`: Loads configuration from YAML.
- `get_config() -> Config`: Returns the singleton config instance.
- `get_species_list() -> List[str]`: Returns configured species.
- `get_data_path() -> Path`: Returns base data directory.

## `code.data.download`

- `download_genomes(species: List[str]) -> Dict[str, Path]`: Fetches genomes.
- `download_metabolites(species: List[str]) -> Dict[str, Path]`: Fetches metabolite data.
- `DownloadError`: Exception for download failures.

## `code.data.preprocess`

- `run_antiSMASH_wrapper(fasta_path: Path) -> Path`: Runs antiSMASH, returns JSON path.
- `harmonize_metabolites(df: pd.DataFrame) -> pd.DataFrame`: Normalizes InChIKeys, log-transforms.
- `map_bgc_to_metabolite(bgc_type: str) -> str`: Maps BGC to metabolite class.

## `code.modeling.phylo`

- `load_phylogeny(tree_path: Path) -> dendropy.Tree`: Loads Newick tree.
- `construct_covariance_matrix(tree: dendropy.Tree) -> np.ndarray`: Builds phylogenetic covariance.
- `train_pgls(X: np.ndarray, y: np.ndarray, cov_matrix: np.ndarray) -> ModelOutput`: Fits PGLS.

## `code.modeling.train`

- `apply_pca(df: pd.DataFrame, n_components: int) -> pd.DataFrame`: Reduces dimensions.
- `train_models_loo(X: np.ndarray, y: np.ndarray) -> Dict[str, ModelOutput]`: LOO cross-validation.
- `create_stratified_split(clades: List[str]) -> Tuple[np.ndarray, np.ndarray]`: Phylo-split.

## `code.modeling.eval`

- `evaluate_models(models: Dict, X_test, y_test) -> Dict[str, float]`: Computes R², correlation.
- `run_sensitivity_sweep(thresholds: List[float]) -> Dict`: Sweeps thresholds.
- `calculate_variation(results: Dict) -> float`: Max R² difference.

## `code.utils.report`

- `generate_report(metrics: Dict, importance: Dict, sensitivity: Dict) -> str`: Formats Markdown.
- `save_report(report: str, path: Path)`: Writes report to disk.
