# Research Implementation Notes: Secondary Outputs

## Purpose

This document provides implementation details for the secondary outputs that address
reviewer concerns. These outputs are not part of the primary validity metrics but
provide additional insights and methodological transparency.

## Experience Trace Implementation (T034)

### Motivation

Dan Rockmore's review highlighted a gap: without a mechanism for tracing which latent
representations correspond to aspects of the reported experience, the internal
structure of phenomenological generation remains opaque.

### Implementation Strategy

The `experience_trace.py` script performs lightweight attention mapping:

1. **Keyword Identification**: Uses the marker dictionary from `config.py` to locate
 phenomenological keywords in generated text.
2. **Attention Extraction**: For each keyword token, extracts attention scores from
 the model's attention heads during generation.
3. **Top-K Selection**: Identifies the k heads with highest activation for each keyword.
4. **Aggregation**: Computes layer-wise averages for summary statistics.

### Limitations

- **Model Access**: Requires access to attention weights, which may not be available
 in all inference setups. The implementation uses `llama-cpp-python` with appropriate
 flags.
- **Approximation**: This is a heuristic approach, not a full mechanistic interpretability
 analysis.
- **Tokenization**: Attention is token-level; subword tokenization may split keywords.

### Output Format

See `data/processed/experience_traces.json` schema in `data-model.md`.

### Usage Example

```python
from analysis.experience_trace import run_experience_trace_analysis

results = run_experience_trace_analysis(
 report_path="data/raw/direct_strategy/samples.json",
 keywords=["feel", "now", "see", "experience"],
 top_k=5
)
```

## Stylistic Comparison Implementation (T035)

### Motivation

David Krakauer's review questioned whether phenomenological reports map onto anything
distinguishable from ordinary language. The stylistic comparison provides an
operational test of this hypothesis.

### Implementation Strategy

The `stylistic_comparison.py` script:

1. **Baseline Selection**: Loads a baseline corpus (IMDB or similar) representing
 "ordinary conversation" or narrative language.
2. **Marker Counting**: Applies the same marker dictionary to both corpora.
3. **Structural Metrics**: Computes sentence length variance, paragraph transitions,
 and other structural features.
4. **Statistical Comparison**: Performs t-tests and computes effect sizes.

### Baseline Corpus Choice

The IMDB dataset is used as a baseline because:
- It contains natural language narratives
- It is readily available via `datasets` library
- It represents a different domain (reviews) from phenomenological reports

Alternative baselines (e.g., CommonCrawl subsets) may be substituted for robustness
checks.

### Output Format

See `data/processed/stylistic_comparison.json` schema in `data-model.md`.

### Usage Example

```python
from analysis.stylistic_comparison import run_stylistic_comparison

results = run_stylistic_comparison(
 phenomenological_path="data/processed/validity_scores.csv",
 baseline_dataset="imdb",
 marker_dict=None # Uses config.py defaults
)
```

## Integration with Primary Analysis

Both secondary outputs are independent of the primary validity metrics but can be
correlated:

- **Experience Traces ↔ Validity Scores**: Do attention patterns predict consistency?
- **Stylistic Comparison ↔ Marker Density**: Is marker density higher in reports
 with higher validity scores?

These correlational analyses are left to researchers as exploratory work.

## Reproducibility

Both scripts are included in the reproducibility archive (T025). The exact baseline
dataset version and marker dictionary used are recorded in the archive manifest.

## Future Extensions

1. **Dynamic Baselines**: Compare against multiple baseline corpora (news, fiction,
 social media) to assess domain specificity.
2. **Temporal Attention**: Track how attention patterns evolve across a report.
3. **Cross-Model Comparison**: Apply experience tracing to different model sizes
 (TinyLlama vs. 7B) to assess architectural effects.