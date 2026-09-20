# Pipeline Architecture

This document describes the architectural components of the llmXive automated research pipeline.

## High-Level Flow

```
┌─────────────────────┐
│ Data Acquisition │ (US1)
│ (01_data_acq.py) │
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ Preprocessing & │
│ Streaming/Sampling │
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ Pattern Mapping │ (US2)
│ (02_pattern_map.py) │
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ Proposal Generation│ (US2)
│ (03_proposal_gen.py)│
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ Evaluation │ (US3)
│ (04_eval_recruit.py)│
└──────────┬──────────┘
 │
 ▼
┌─────────────────────┐
│ Statistical │ (US3)
│ Analysis │
│ (05_stat_analysis.py)│
└─────────────────────┘
```

## Component Details

### 1. Data Acquisition (`code/01_data_acquisition.py`)

**Responsibilities**:
- Fetch abstracts from arXiv (ML) and non-ML sources
- Validate fetch status (fail loudly on 403/404)
- Stream and sample data to respect memory constraints
- Preprocess and normalize text

**Key Functions**:
- `stream_arxiv_abstracts()`: Paginated arXiv API calls
- `stream_doi_entries()`: DOI-based fetching for non-ML sources
- `stream_and_sample(n=500, seed=42)`: Memory-safe sampling
- `validate_fetch_status()`: Strict error handling
- `preprocess_corpus()`: Text normalization

**Outputs**:
- `data/raw/corpus_raw.jsonl`: Raw fetched data
- `data/processed/corpus.jsonl`: Cleaned corpus

### 2. Pattern Mapping (`code/02_pattern_mapping.py`)

**Responsibilities**:
- Generate embeddings for pattern cards
- Retrieve top-k patterns for problem statements
- Validate two-group design constraints

**Key Functions**:
- `get_model()`: Load quantized sentence-transformers
- `encode_text()`: Generate embeddings
- `retrieve_top_k_patterns()`: Cosine similarity matching
- `validate_group_config()`: Enforce two-group design

**Outputs**:
- Pattern mappings for each problem statement
- `data/processed/holdout_patterns.json`: Hold-out set for validation

### 3. Proposal Generation (`code/03_proposal_generation.py`)

**Responsibilities**:
- Generate pattern-guided proposals
- Generate baseline proposals
- Batch processing for memory efficiency
- Pair proposals and save results

**Key Functions**:
- `generate_proposal_text()`: LLM-based generation
- `generate_proposals()`: Batch processing loop
- `save_proposals()`: Output to JSONL

**Outputs**:
- `data/results/generated_proposals.jsonl`: Paired proposals

### 4. Evaluation (`code/04_evaluation_recruitment.py`)

**Responsibilities**:
- Generate recruitment payloads
- Validate expert inputs
- Load and ingest expert ratings

**Key Functions**:
- `generate_ratings_template()`: Create blinded evaluation template
- `validate_expert_inputs()`: Cross-reference expert roster
- `ingest_ratings()`: Load collected ratings

**Outputs**:
- `data/results/recruitment_payload.json`: Job posting data
- `data/results/ratings_filled.csv`: Expert ratings

### 5. Statistical Analysis (`code/05_statistical_analysis.py`)

**Responsibilities**:
- Calculate Inter-Rater Reliability (Krippendorff's alpha)
- Perform normality checks
- Select appropriate statistical test (t-test vs. Wilcoxon)
- Conduct sensitivity analysis
- Apply multiple comparison correction
- Generate final report

**Key Functions**:
- `calculate_irr()`: Krippendorff's alpha
- `perform_statistical_test()`: Dynamic test selection
- `sensitivity_analysis()`: Outlier removal and re-test
- `apply_correction()`: Bonferroni/Benjamini-Hochberg
- `generate_final_report()`: Report creation

**Outputs**:
- `data/results/validity_metrics.json`: Effect sizes
- `data/results/sensitivity_analysis_report.md`: Robustness analysis
- `data/results/analysis_report.md`: Final results

## Utility Modules

### `code/utils/config.py`
- Seed pinning (numpy, torch, python)
- Model configuration and fallback logic
- Environment hashing

### `code/utils/error_handling.py`
- Custom exceptions (`DataFetchError`, `ValidationError`)
- Strict fetch handling
- Error logging

### `code/utils/logging_config.py`
- Logger initialization
- PII filtering
- Model fallback logging

### `code/utils/benchmark_profiler.py`
- Runtime and memory profiling
- Phase-level metrics

### `code/utils/caching.py`
- Intermediate result caching
- Embedding cache
- Prompt cache

### `code/utils/update_state.py`
- Artifact versioning
- State management
- Manifest updates

## Data Flow

1. **Raw Data**: Fetched from APIs → `data/raw/corpus_raw.jsonl`
2. **Processed Data**: Normalized, validated → `data/processed/corpus.jsonl`
3. **Hold-out Set**: Split for validation → `data/processed/holdout_patterns.json`
4. **Generated Proposals**: Paired outputs → `data/results/generated_proposals.jsonl`
5. **Expert Ratings**: Collected evaluations → `data/results/ratings_filled.csv`
6. **Analysis Results**: Statistical outputs → `data/results/analysis_report.md`

## Error Handling Strategy

- **Data Fetch Failures**: Immediate halt with venue context
- **IRR Gate Failures**: Pipeline stops if alpha < 0.6
- **Power Constraint Violations**: Flag as "underpowered"
- **Memory Constraints**: Stream/sample; fail if exceeded
- **Two-Group Violations**: Reject any non-compliant configurations

## Security Considerations

- PII detection and sanitization in logs and outputs
- Blinded proposal IDs for expert ratings
- Verified expert roster cross-referencing
- No synthetic data fallbacks

## Performance Constraints

- **Memory**: <7 GB RAM (CPU execution)
- **Runtime**: <6 hours total pipeline
- **Sample Size**: n=50 pairs (justified by power analysis)
- **Embeddings**: Quantized model for CPU tractability
