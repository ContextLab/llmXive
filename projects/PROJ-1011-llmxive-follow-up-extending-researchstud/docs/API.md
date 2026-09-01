# llmXive API Reference

This document details the public interfaces for the llmXive automated science pipeline.

## Core Modules

### `code/01_data_acquisition.py`

Responsible for fetching, streaming, and preprocessing scientific abstracts.

#### Public Functions

- `normalize_text(text: str) -> str`
 Normalizes Unicode and removes non-printable characters.
- `is_valid_abstract(text: str) -> bool`
 Checks if the abstract is non-empty and meets length constraints.
- `filter_malformed_entries(entries: List[Dict]) -> List[Dict]`
 Filters out entries with missing required fields.
- `preprocess_corpus(raw_data: List[Dict]) -> List[Dict]`
 Applies normalization and validation to the entire corpus.
- `validate_fetch_status(response: requests.Response, venue: str) -> None`
 Raises `DataFetchError` on 403/404 or paywall detection.
- `load_data_sources_config(path: str) -> Dict`
 Loads and validates the `data-sources.yaml` configuration.
- `stream_arxiv_abstracts(category: str, max_results: int) -> Generator`
 Streams arXiv abstracts for a given category (e.g., `cs.LG`).
- `stream_doi_entries(source_config: Dict) -> Generator`
 Streams entries from DOI-based sources (Nature, Health Affairs).
- `stream_and_sample(n: int, seed: int) -> List[Dict]`
 Streams data and samples `n` rows while maintaining domain balance.
- `save_corpus_streaming(data: List[Dict], output_path: str) -> None`
 Saves the processed corpus to a JSONL file.

### `code/02_pattern_mapping.py`

Handles embedding generation and pattern retrieval.

#### Public Functions

- `get_model(model_name: str) -> SentenceTransformer`
 Loads the embedding model (supports quantization).
- `encode_text(model, texts: List[str]) -> np.ndarray`
 Generates embeddings for a list of texts.
- `cosine_similarity_matrix(emb1: np.ndarray, emb2: np.ndarray) -> np.ndarray`
 Computes cosine similarity between two sets of embeddings.
- `retrieve_top_k_patterns(query_text: str, patterns: List[Dict], k: int) -> List[Dict]`
 Returns top-k patterns similar to the query text.

### `code/03_proposal_generation.py`

Generates research proposals based on patterns or baseline prompts.

#### Public Functions

- `load_processed_corpus(path: str) -> List[Dict]`
 Loads the preprocessed corpus from disk.
- `load_pattern_map(path: str) -> Dict`
 Loads the pattern mapping configuration.
- `generate_proposal_text(problem: str, pattern: Optional[Dict]) -> str`
 Generates a single proposal text.
- `generate_proposals(corpus: List[Dict], mode: str) -> List[Dict]`
 Generates proposals for the entire corpus in 'pattern-guided' or 'baseline' mode.
- `save_proposals(proposals: List[Dict], output_path: str) -> None`
 Saves proposals to a JSONL file.

### `code/04_evaluation_recruitment.py`

Manages expert recruitment and rating ingestion.

#### Public Functions

- `load_expert_roster(path: str) -> List[Dict]`
 Loads the verified expert roster.
- `validate_expert_inputs(ratings: List[Dict], roster: List[Dict]) -> None`
 Validates that ratings correspond to verified experts.
- `generate_ratings_template(proposals: List[Dict], output_path: str) -> None`
 Creates a blinded CSV template for expert rating.
- `ingest_ratings(csv_path: str) -> List[Dict]`
 Loads and validates ratings from a filled CSV.

### `code/05_statistical_analysis.py`

Performs statistical analysis and report generation.

#### Public Functions

- `calculate_krippendorff_alpha(ratings: List[Dict]) -> float`
 Calculates Inter-Rater Reliability.
- `perform_normality_test(scores: List[float]) -> bool`
 Checks for normality (Shapiro-Wilk).
- `run_statistical_test(group1: List[float], group2: List[float]) -> Dict`
 Runs t-test or Wilcoxon based on normality.
- `apply_multiple_comparison_correction(p_values: List[float]) -> List[float]`
 Applies Bonferroni or Benjamini-Hoch correction.
- `generate_analysis_report(results: Dict, output_path: str) -> None`
 Generates the final markdown report.

## Utilities

### `code/utils/config.py`
- `set_seed(seed: int)`: Sets seeds for reproducibility.
- `select_model_on_memory_error(e: Exception) -> str`: Selects a fallback model on OOM.

### `code/utils/error_handling.py`
- `DataFetchError`: Custom exception for data acquisition failures.
- `ValidationError`: Custom exception for input validation failures.

### `code/utils/benchmark_profiler.py`
- `profile_phase(phase_name: str, func: Callable)`: Profiles runtime and memory.

## Data Models

All models are defined in `code/models/`.

- `Abstract`: Represents a scientific abstract.
- `PatternCard`: Represents a research pattern.
- `Proposal`: Represents a generated research proposal.
- `Rating`: Represents an expert rating.
