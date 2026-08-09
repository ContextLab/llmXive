# llmXive API Documentation

This document provides function signatures and module descriptions for the llmXive automated science pipeline, specifically for the "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills" follow-up project.

## Module: `src.ingestion.download_weights`

Handles fetching LoRA weights from HuggingFace datasets or generating documented proxies.

- `load_real_weights(dataset_id: str, path: str) -> Dict[str, np.ndarray]`
 - Downloads and loads real LoRA A/B matrices from a specified HuggingFace dataset.
- `generate_proxy_weights(shape: Tuple[int, int], seed: int = 42, mean: float = 0.0, std: float = 1.0) -> np.ndarray`
 - Generates a proxy weight matrix using `numpy.random.normal` preserving statistical properties (mean, variance) and shape.
- `save_weights(data: Dict[str, Any], output_path: Path, is_proxy: bool = False) -> None`
 - Saves weights to `.npz` format with metadata flags.
- `process_dataset(dataset_config: Dict[str, Any]) -> None`
 - Orchestrates loading or proxy generation for a specific dataset configuration.
- `main() -> None`
 - Entry point for the script.

## Module: `src.ingestion.flatten_lora`

Flattens LoRA A/B matrices into normalized high-dimensional vectors.

- `load_lora_matrices(weight_path: Path) -> Tuple[np.ndarray, np.ndarray]`
 - Loads A and B matrices from an `.npz` file.
- `flatten_and_normalize(a_matrix: np.ndarray, b_matrix: np.ndarray) -> np.ndarray`
 - Flattens matrices to 1D, concatenates, and applies L2 normalization.
- `validate_dimensions(vectors: List[np.ndarray]) -> bool`
 - Ensures all vectors have consistent dimensions.
- `log_ingestion_metrics(vectors_processed: int, index_size_mb: float) -> None`
 - Logs metrics for ingestion performance.

## Module: `src.retrieval.vector_db`

Constructs and manages the static CPU-compatible skill index.

- `load_flattened_vectors(data_dir: Path) -> List[np.ndarray]`
 - Loads flattened vectors from the ingestion output directory.
- `compute_index_structure(vectors: List[np.ndarray]) -> Dict[str, Any]`
 - Computes index metadata (dimensionality, count, checksums).
- `prepare_for_serialization(vectors: List[np.ndarray], metadata: Dict[str, Any]) -> np.ndarray`
 - Prepares data array and metadata for saving.
- `save_index(data: np.ndarray, metadata: Dict[str, Any], output_path: Path) -> None`
 - Saves the static index to `data/processed/skill_index.npz`.
- `main() -> None`
 - Entry point for index construction.

## Module: `src.retrieval.query`

Generates query vectors and retrieves nearest neighbors.

- `generate_query_vector(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray`
 - Generates a text embedding for a query string.
- `measure_embedding_latency() -> float`
 - Measures wall-clock latency for text embedding generation.
- `retrieve_nearest_neighbors(query_vector: np.ndarray, index: np.ndarray, k: int = 5) -> List[Tuple[int, float]]`
 - Retrieves indices and cosine similarities of the k-nearest neighbors.
- `main() -> None`
 - Entry point for query execution.

## Module: `src.retrieval.strategies`

Implements synthesis strategies for LoRA adapters.

- `load_skill_index(index_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]`
 - Loads the skill index and metadata.
- `load_query_embeddings(query_path: Path) -> np.ndarray`
 - Loads pre-computed query embeddings.
- `get_skill_metadata(index_metadata: Dict[str, Any]) -> Dict[str, Any]`
 - Extracts skill metadata for a given index.
- `single_nearest_neighbor(query_vector: np.ndarray, index: np.ndarray) -> np.ndarray`
 - Returns the single nearest neighbor weight vector.
- `unweighted_mean(vectors: List[np.ndarray]) -> np.ndarray`
 - Computes the arithmetic mean of k-top vectors.
- `cosine_weighted_average(vectors: List[np.ndarray], similarities: List[float]) -> np.ndarray`
 - Computes a cosine-similarity weighted average of vectors.
- `synthesize_adapter(strategy: str, query_vector: np.ndarray, index: np.ndarray, k: int = 5) -> np.ndarray`
 - Orchestrates the synthesis based on the selected strategy.
- `reconstruct_matrices(flat_vector: np.ndarray, shape_a: Tuple[int, int], shape_b: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]`
 - Reconstructs A and B matrices from a flattened vector.
- `save_synthesized_adapter(a_matrix: np.ndarray, b_matrix: np.ndarray, output_path: Path) -> None`
 - Saves synthesized weights to `artifacts/synthesized_adapters/`.
- `main() -> None`
 - Entry point for synthesis execution.

## Module: `src.validation.generate_ground_truth`

Generates synthetic "true weights" for known composite tasks.

- `interpolate_weights(weight_a: np.ndarray, weight_b: np.ndarray, alpha: float = 0.5) -> np.ndarray`
 - Computes `W_syn = alpha * W_A + (1-alpha) * W_B`.
- `generate_composite_ground_truth(tasks: List[Dict[str, Any]]) -> np.ndarray`
 - Generates ground truth for a list of composite task definitions.
- `save_ground_truth(data: np.ndarray, output_path: Path) -> None`
 - Saves ground truth to `data/processed/composite_ground_truth.npz`.

## Module: `src.validation.reconstruction_error`

Calculates reconstruction error between synthesized and true weights.

- `flatten_matrices(a: np.ndarray, b: np.ndarray) -> np.ndarray`
 - Flattens A and B matrices into a single vector for comparison.
- `calculate_cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float`
 - Computes cosine distance between two vectors.
- `compute_error(synthesized_path: Path, ground_truth_path: Path) -> float`
 - Loads weights and computes the error metric.
- `save_error_report(error_value: float, output_path: Path) -> None`
 - Saves the error to `data/results/reconstruction_error.json`.

## Module: `src.validation.linearity_check`

Validates the linearity assumption between text-space and weight-space distances.

- `calculate_pearson_correlation(x: List[float], y: List[float]) -> float`
 - Computes Pearson correlation coefficient.
- `check_linearity(task_pairs_path: Path) -> Dict[str, Any]`
 - Computes correlation and validity flag (True if >= 0.6).
- `save_linearity_report(report: Dict[str, Any], output_path: Path) -> None`
 - Saves results to `data/results/linearity_check.json`.

## Module: `src.evaluation.runner`

Executes environment logic and evaluation loops.

- `check_memory_usage() -> float`
 - Checks current memory usage and fails if > 6.5 GB.
- `load_synthesized_adapter(adapter_path: Path) -> Tuple[np.ndarray, np.ndarray]`
 - Loads synthesized A/B matrices.
- `apply_lora_to_model(model_path: Path, a_matrix: np.ndarray, b_matrix: np.ndarray) -> Any`
 - Applies LoRA weights to the base GGUF model.
- `execute_environment_logic(task: str, model: Any) -> bool`
 - Runs the environment logic (ALFWorld/Search-QA) and returns success.
- `run_evaluation(adapter_path: Path, task: str, num_trials: int = 5) -> Dict[str, Any]`
 - Runs multiple trials and calculates mean success probability.
- `main() -> None`
 - Entry point for evaluation.

## Module: `src.evaluation.stats`

Performs statistical testing and corrections.

- `paired_t_test(group_a: List[float], group_b: List[float]) -> float`
 - Performs a paired t-test and returns p-value.
- `wilcoxon_signed_rank(group_a: List[float], group_b: List[float]) -> float`
 - Performs Wilcoxon signed-rank test and returns p-value.
- `benjamini_hochberg(p_values: List[float]) -> List[float]`
 - Applies Benjamini-Hochberg correction to a list of p-values.
- `generate_stats_report(results: Dict[str, Any]) -> Dict[str, Any]`
 - Aggregates p-values, q-values, and other metrics into a report.

## Module: `src.evaluation.report_generator`

Generates final statistical reports.

- `load_json_safe(path: Path) -> Dict[str, Any]`
 - Safely loads a JSON file.
- `aggregate_results(reports: List[Dict[str, Any]]) -> Dict[str, Any]`
 - Aggregates multiple result dictionaries into a single report.
- `main() -> None`
 - Entry point for report generation.

## Module: `src.validate.citation_check`

Verifies dataset sources and URLs.

- `load_data_sources(config_path: Path) -> Dict[str, Any]`
 - Loads `data_sources.yaml`.
- `check_url_reachability(url: str) -> bool`
 - Performs HTTP 200 check on a URL.
- `check_hf_dataset_files(dataset_id: str, paths: List[str]) -> bool`
 - Validates the existence of specific files within a HuggingFace dataset.
- `verify_sources() -> bool`
 - Orchestrates verification for all defined sources.
- `main() -> None`
 - Entry point for citation checking.

## Module: `src.utils.config`

Configuration management.

- `get_seed() -> int`
 - Returns the pinned random seed.
- `get_path(key: str) -> Path`
 - Resolves a path key to an absolute `Path` object.
- `load_env_vars() -> None`
 - Loads environment variables from `.env`.

## Module: `src.utils.versioning`

Artifact versioning and hashing.

- `compute_sha256(file_path: Path) -> str`
 - Computes SHA256 hash of a file.
- `update_state_file(state_path: Path, artifact_path: Path, hash: str) -> None`
 - Updates the project state YAML with artifact hashes.