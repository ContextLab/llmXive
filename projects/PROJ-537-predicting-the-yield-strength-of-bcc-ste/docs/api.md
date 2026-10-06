# API Documentation

This document provides function signatures and usage details for the core modules
in the `code/` directory.

---

## Ingestion Module (`code/ingestion/`)

### `fetch_experimental.py`

Downloads and processes experimental yield strength data from external sources.

```python
def download_experimental_data(url: str, output_path: Path) -> pd.DataFrame:
 """
 Downloads the experimental dataset from the specified URL.

 Args:
 url: The URL to download data from (from CONFIG.EXPERIMENTAL_DATA_URL).
 output_path: Local path to save the raw CSV.

 Returns:
 DataFrame containing the raw experimental data.
 """

def fetch_experimental_data() -> pd.DataFrame:
 """
 Orchestrates the download and initial loading of experimental data.

 Returns:
 DataFrame with experimental yield strength data.
 """

def main():
 """Entry point for the script."""
```

### `fetch_dft.py`

Queries the Materials Project API for DFT elastic constants.

```python
def get_session_with_retry() -> requests.Session:
 """
 Creates a requests session with exponential backoff retry logic.

 Returns:
 Configured requests.Session object.
 """

def fetch_elastic_data(material_id: str, api_key: str) -> Dict[str, Any]:
 """
 Fetches elastic tensor data for a specific material ID.

 Args:
 material_id: Materials Project ID (e.g., 'mp-134').
 api_key: Valid Materials Project API key.

 Returns:
 Dictionary containing elastic constants and metadata.
 """

def fetch_dft_data() -> List[Dict[str, Any]]:
 """
 Iterates through the experimental list to fetch corresponding DFT data.

 Returns:
 List of dictionaries containing DFT elastic properties.
 """

def main():
 """Entry point for the script."""
```

### `merge_and_filter.py`

Merges experimental and DFT datasets, filters for BCC structure, and handles data cleaning.

```python
def parse_range_value(value: str) -> Tuple[float, float, bool]:
 """
 Parses range strings (e.g., '200-250') into midpoint and flags.

 Args:
 value: String value which may be a range.

 Returns:
 Tuple of (midpoint, original_value_as_float_if_single, is_range_flag).
 """

def load_experimental_data(path: Path) -> pd.DataFrame:
 """Loads the raw experimental CSV."""

def load_dft_data(path: Path) -> pd.DataFrame:
 """Loads the raw DFT JSON/CSV data."""

def filter_bcc_structure(df: pd.DataFrame) -> pd.DataFrame:
 """
 Filters the dataset to include only Space Group 229 (BCC).

 Args:
 df: Input DataFrame with 'space_group' column.

 Returns:
 Filtered DataFrame.
 """

def merge_datasets(exp_df: pd.DataFrame, dft_df: pd.DataFrame) -> pd.DataFrame:
 """
 Performs an inner join on material composition/ID.

 Returns:
 Merged DataFrame.
 """

def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
 """
 Handles missing values: drops rows with null yield strength or shear modulus.

 Returns:
 Cleaned DataFrame.
 """

def validate_merged_dataset(df: pd.DataFrame) -> bool:
 """
 Validates that the dataset has >= 20 rows.

 Raises:
 ERR_INSUFFICIENT_DATA if row count < 20.
 """

def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
 """Saves the final merged dataset to CSV."""

def main():
 """Entry point for the script."""
```

### `finalize_dataset.py`

```python
def validate_and_save_merged_dataset(input_path: Path, output_path: Path) -> None:
 """
 Orchestrates the final validation and saving of the merged dataset.

 Raises:
 ERR_INSUFFICIENT_DATA if validation fails.
 """

def main():
 """Entry point for the script."""
```

### `generate_checksums.py`

```python
def generate_all_checksums(directory: Path) -> Dict[str, str]:
 """
 Generates SHA-256 checksums for all files in a directory.

 Returns:
 Dictionary mapping relative file paths to checksums.
 """

def write_checksums_file(checksums: Dict[str, str], output_path: Path) -> None:
 """Writes checksums to a text file."""

def main():
 """Entry point for the script."""
```

### `update_state.py`

```python
def load_checksums(path: Path) -> Dict[str, str]:
 """Loads checksums from a file."""

def load_or_create_state(state_path: Path) -> Dict[str, Any]:
 """Loads existing state YAML or creates a new one."""

def update_state_with_checksums(state: Dict, checksums: Dict[str, str]) -> None:
 """Updates the state dictionary with new artifact hashes."""

def save_state(state: Dict, path: Path) -> None:
 """Saves the state dictionary to YAML."""

def main():
 """Entry point for the script."""
```

---

## Modeling Module (`code/modeling/`)

### `features.py`

Feature engineering for composition and DFT descriptors.

```python
def parse_element_column(col: pd.Series) -> pd.DataFrame:
 """
 Parses element composition strings (e.g., 'Fe0.9Cr0.1') into separate columns.

 Returns:
 DataFrame with one column per element (atomic fraction).
 """

def encode_composition(df: pd.DataFrame) -> pd.DataFrame:
 """
 Encodes composition data using one-hot encoding and atomic fractions.

 Returns:
 DataFrame with encoded features.
 """

def normalize_dft_descriptors(df: pd.DataFrame) -> pd.DataFrame:
 """
 Normalizes DFT features (Shear Modulus, Bulk Modulus) using StandardScaler.

 Returns:
 DataFrame with normalized DFT features.
 """

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
 """
 Calculates Variance Inflation Factors for multicollinearity check.

 Returns:
 Series of VIF values for each feature.
 """

def prepare_modeling_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
 """
 Prepares the final feature matrix X and target vector y.

 Returns:
 Tuple of (X, y).
 """

def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
 """Returns the full feature matrix."""

def main():
 """Entry point for the script."""
```

### `train.py`

Training pipeline for Random Forest models.

```python
def train_random_forest_cv(X: np.ndarray, y: np.ndarray, model_type: str = 'rf') -> Dict[str, Any]:
 """
 Trains a Random Forest model with k-fold cross-validation.

 Args:
 X: Feature matrix.
 y: Target vector.
 model_type: 'rf_baseline' (composition only) or 'rf_dft' (with DFT features).

 Returns:
 Dictionary containing the trained model, CV scores, and metadata.
 """

def run_training_pipeline(data_path: Path, output_dir: Path) -> None:
 """
 Orchestrates feature preparation, model training, and saving results.
 """

def main():
 """Entry point for the script."""
```

### `evaluate.py`

Evaluation metrics and statistical testing.

```python
def load_models(path: Path) -> Dict[str, Any]:
 """Loads trained models from pickle files."""

def load_cv_results(path: Path) -> Dict[str, Any]:
 """Loads cross-validation results."""

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
 """
 Calculates R² and MAE.

 Returns:
 Dictionary with 'r2' and 'mae'.
 """

def perform_paired_ttest(errors_baseline: np.ndarray, errors_dft: np.ndarray) -> Dict[str, float]:
 """
 Performs a paired t-test on fold-wise errors.

 Returns:
 Dictionary with 't_statistic' and 'p_value'.
 """

def calculate_statistical_power(effect_size: float, n: int, alpha: float = 0.05) -> float:
 """
 Calculates statistical power (1 - beta) for the t-test.

 Returns:
 Power value (0.0 to 1.0).
 """

def calculate_shear_yield_correlation(df: pd.DataFrame) -> float:
 """
 Calculates Pearson correlation between Shear Modulus and Yield Strength.

 Returns:
 Correlation coefficient.
 """

def run_evaluation(data_path: Path, results_path: Path) -> Dict[str, Any]:
 """
 Orchestrates the full evaluation pipeline and saves results.
 """

def save_results(metrics: Dict[str, Any], output_path: Path) -> None:
 """Saves evaluation metrics to JSON."""

def main():
 """Entry point for the script."""
```

### `calculate_correlation.py`

```python
def load_merged_data(path: Path) -> pd.DataFrame:
 """Loads the merged dataset."""

def calculate_pearson_correlation(df: pd.DataFrame, col_x: str, col_y: str) -> Tuple[float, float]:
 """
 Calculates Pearson correlation and p-value.

 Returns:
 Tuple of (correlation, p_value).
 """

def run_correlation_analysis(data_path: Path) -> Dict[str, Any]:
 """Runs the correlation analysis and returns results."""

def main():
 """Entry point for the script."""
```

### `save_results.py`

```python
def load_schema_contracts(schema_path: Path) -> Dict[str, Any]:
 """Loads the output schema contract."""

def validate_output_against_schema(data: Dict, schema: Dict) -> bool:
 """Validates output data against the schema."""

def assemble_final_metrics(eval_results: Dict, correlation_results: Dict) -> Dict[str, Any]:
 """Combines all results into the final output structure."""

def write_output_json(data: Dict, output_path: Path) -> None:
 """Writes the final metrics to JSON."""

def main():
 """Entry point for the script."""
```

---

## Interpretability Module (`code/interpretability/`)

### `shap_analysis.py`

TreeSHAP and permutation importance analysis.

```python
def load_preprocessed_data(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
 """Loads X, y, and feature names."""

def load_trained_model(path: Path) -> Any:
 """Loads the trained Random Forest model."""

def calculate_shap_values(model: Any, X: np.ndarray) -> np.ndarray:
 """
 Calculates TreeSHAP values.

 Returns:
 Array of SHAP values.
 """

def calculate_permutation_importance(model: Any, X: np.ndarray, y: np.ndarray) -> np.ndarray:
 """
 Calculates permutation importance.

 Returns:
 Array of importance scores.
 """

def analyze_feature_importance(shap_values: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
 """
 Analyzes and ranks feature importance based on SHAP values.

 Returns:
 DataFrame with feature names and importance scores.
 """

def generate_shap_plots(shap_values: np.ndarray, X: np.ndarray, feature_names: List[str], output_dir: Path) -> None:
 """Generates SHAP summary plots and saves them."""

def save_shap_results(results: Dict[str, Any], output_path: Path) -> None:
 """Saves SHAP results to JSON/Pickle."""

def run_shap_analysis(model_path: Path, data_path: Path, output_dir: Path) -> None:
 """Orchestrates the full SHAP analysis pipeline."""

def main():
 """Entry point for the script."""
```

### `bootstrap_stability.py`

Bootstrap stability analysis.

```python
def load_data_and_model(data_path: Path, model_path: Path) -> Tuple[np.ndarray, np.ndarray, Any]:
 """Loads data and model for stability analysis."""

def run_sample_size_sweep(X: np.ndarray, y: np.ndarray, model_class, min_n: int, max_n: int, steps: int) -> Dict[str, Any]:
 """
 Runs a sample-size sweep (n=10 to n=50) to calculate std_dev of feature importance.

 Returns:
 Dictionary with std_dev results per sample size.
 """

def run_fixed_sample_bootstrap(X: np.ndarray, y: np.ndarray, model_class, n_iterations: int = 10) -> Dict[str, Any]:
 """
 Runs 10 bootstrapped samples of the full dataset.

 Returns:
 Dictionary with feature importance distributions.
 """

def check_stability(importance_results: Dict[str, np.ndarray], threshold: float = 0.05) -> bool:
 """
 Checks if std_dev of key DFT descriptors is below threshold.

 Returns:
 Boolean indicating stability.
 """

def save_results(results: Dict[str, Any], output_path: Path) -> None:
 """Saves stability analysis results."""

def main():
 """Entry point for the script."""
```

### `check_stability.py`

```python
def load_bootstrap_results(path: Path) -> Dict[str, Any]:
 """Loads bootstrap results."""

def check_dft_stability(results: Dict[str, Any], threshold: float = 0.05) -> Dict[str, Any]:
 """
 Checks specific DFT descriptors for stability.

 Returns:
 Dictionary with 'is_stable' boolean and details.
 """

def save_stability_check(check_results: Dict[str, Any], output_path: Path) -> None:
 """Saves the stability check results."""

def main():
 """Entry point for the script."""
```

### `finalize_output.py`

```python
def load_json_safe(path: Path) -> Dict[str, Any]:
 """Loads a JSON file safely."""

def load_pickle_safe(path: Path) -> Any:
 """Loads a pickle file safely."""

def assemble_success_criteria(shap_results: Dict, stability_results: Dict, eval_results: Dict) -> Dict[str, Any]:
 """
 Assembles all success criteria (SC-001 to SC-008) into the final output.

 Returns:
 Dictionary containing all success criteria.
 """

def main():
 """Entry point for the script."""
```

### `plot_results.py`

```python
def load_shap_results(path: Path) -> Dict[str, Any]:
 """Loads SHAP results."""

def load_bootstrap_results(path: Path) -> Dict[str, Any]:
 """Loads bootstrap stability results."""

def generate_shap_summary_plot(shap_values: np.ndarray, feature_names: List[str], output_path: Path) -> None:
 """Generates and saves the SHAP summary plot."""

def generate_stability_distribution_plot(importance_dists: Dict[str, np.ndarray], output_path: Path) -> None:
 """Generates and saves the stability distribution plot."""

def main():
 """Entry point for the script."""
```