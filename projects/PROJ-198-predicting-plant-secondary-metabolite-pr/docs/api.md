# API Reference

This document describes the public API of the `code` package.

## Configuration

### `code.config`

- `load_config(path: str) -> Config`: Load configuration from YAML.
- `get_config() -> Config`: Get the current global config.
- `get_species_list() -> List[str]`: Get list of species from config.
- `get_data_path() -> Path`: Get the root data directory.

## Data Module

### `code.data.download`

- `download_genomes(species: List[str]) -> Dict[str, Path]`: Download genome assemblies.
- `download_metabolites(species: List[str]) -> Dict[str, Path]`: Download metabolite tables.

### `code.data.preprocess`

- `run_antiasmh_wrapper(fasta_path: Path) -> Path`: Run AntiSMASH on a genome.
- `harmonize_metabolites(df: pd.DataFrame) -> pd.DataFrame`: Normalize InChIKeys and log-transform.
- `map_bgc_to_metabolite(bgc_type: str) -> str`: Map BGC type to metabolite class.

### `code.data.align`

- `align_data(genome_data: Dict, metabolite_data: Dict) -> pd.DataFrame`: Merge and filter data.
- `save_aligned_matrix(df: pd.DataFrame, path: Path)`: Save aligned data to CSV.

## Modeling Module

### `code.modeling.phylo`

- `load_phylogeny(path: Path) -> dendropy.Tree`: Load phylogenetic tree.
- `construct_covariance_matrix(tree: dendropy.Tree) -> np.ndarray`: Build covariance matrix.
- `train_pgls(X: np.ndarray, y: np.ndarray, phylo_matrix: np.ndarray) -> ModelOutput`: Train PGLS model.

### `code.modeling.train`

- `apply_pca(df: pd.DataFrame, n_components: int) -> pd.DataFrame`: Apply PCA.
- `create_stratified_split(df: pd.DataFrame, tree: dendropy.Tree) -> Tuple[np.ndarray, np.ndarray]`: Split by clade.
- `train_models_loo(X: np.ndarray, y: np.ndarray) -> Dict[str, ModelOutput]`: Train with LOO CV.

### `code.modeling.eval`

- `evaluate_models(models: Dict, X_test: np.ndarray, y_test: np.ndarray) -> Dict`: Calculate metrics.
- `run_phylogenetic_permutation(X: np.ndarray, y: np.ndarray, tree: dendropy.Tree) -> float`: Baseline R².
- `run_sensitivity_sweep(thresholds: List[float]) -> Dict`: Run threshold sweep.

## Models

### `code.models.species`

- `Species`: Pydantic model for species metadata.

### `code.models.bgc`

- `BGCFeature`: Pydantic model for BGC features.

### `code.models.metabolite`

- `Metabolite`: Pydantic model for metabolite data.

## Utilities

### `code.utils.logging`

- `setup_logging(level: int)`: Configure logging handlers.
- `get_logger(name: str) -> logging.Logger`: Get a logger instance.

### `code.utils.anti_smash_parser`

- `parse_anti_smash_json(json_path: Path) -> Dict`: Parse AntiSMASH output.
