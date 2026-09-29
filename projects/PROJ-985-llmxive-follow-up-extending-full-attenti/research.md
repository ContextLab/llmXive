# llmXive Research Documentation

## Overview

This document describes the research methodology, experimental design, and statistical analysis for the llmXive project, which evaluates static sparsification techniques against full attention baselines.

## Research Question

Can static linguistic heuristics (e.g., entropy, POS tags, local semantic density) effectively predict token importance in long-context language models, achieving comparable performance to learned attention-based methods (RTPurbo) while being significantly faster and more interpretable?

## Hypotheses

- **H1**: Static heuristics can achieve performance within 1% of learned methods (perplexity and exact match).
- **H2**: The performance gap is not statistically significant (p > 0.05).
- **H3**: Static methods offer deterministic, reproducible results across different random seeds.

## Methodology

### Dataset

- **Source**: RULER dataset (long-context synthetic tasks)
- **Processing**: Streaming load to manage memory constraints (< 7GB RAM)
- **Sample Size**: 100 documents for ground truth extraction, with anomaly exclusion

### Ground Truth Extraction

1. **Model**: Frozen Llama-3-8B (CPU-only, `n_gpu_layers=0`, `n_ctx=4096`)
2. **Method**: RTPurbo (k=10, threshold=0.05) to identify important tokens
3. **Anomaly Detection**: Exclude documents with zero RTPurbo tokens

### Feature Engineering

Static features computed for each token:
- **Entropy**: Shannon entropy of token probability distribution
- **POS Tags**: Part-of-speech labels via spaCy
- **Position**: Token position in document
- **KenLM Perplexity**: N-gram language model perplexity
- **Local Semantic Density**: Density of unique 3-grams in a sliding window (size=10)

### Static Predictor Training

- **Algorithm**: Decision Tree and Logistic Regression
- **Training**: Stratified train/test split with multiple random seeds (42, 123, 456, 789, 101)
- **Rule Derivation**: Extract deterministic rules from decision tree paths

### Baseline Comparison

1. **Full Attention**: Baseline with all tokens
2. **Learned (RTPurbo)**: Multiple seed evaluations for variance estimation
3. **Static Heuristic**: Rule-based token selection

### Metrics

- **Perplexity**: Language model perplexity on held-out tokens
- **Exact Match**: Task-specific exact match score
- **Statistical Significance**: Paired t-test (scipy.stats.ttest_rel)

## Experimental Design

### Reproducibility

- Fixed random seeds for all stochastic operations
- Deterministic data loading and processing pipelines
- Version-controlled dependencies via `requirements.txt`

### Statistical Rigor

- **Paired t-test**: Compare learned vs. static on the same documents
- **Variance Estimation**: Multiple seed runs for learned baseline
- **Falsifiability Check**: Performance drop threshold (1%) and p-value (> 0.05)

### Memory Constraints

- Streaming dataset loading to stay under 7GB RAM
- Chunk-based processing for large documents
- Memory monitoring via `tracemalloc` and `psutil`

## Results

### Performance Summary

| Method | Perplexity | Exact Match | Std Dev |
|--------|------------|-------------|---------|
| Full Attention | [Value] | [Value] | [Value] |
| Learned (RTPurbo) | [Value] | [Value] | [Value] |
| Static Heuristic | [Value] | [Value] | [Value] |

### Statistical Significance

- **P-value**: [Value] (from paired t-test)
- **Performance Drop**: [Value]% (Learned vs. Static)
- **Verdict**: [Negligible/Significant] based on threshold and p-value

### Anomaly Analysis

- Documents excluded: [Count]
- Common anomaly patterns: [Description]

## Discussion

### Interpretability

Static heuristics provide explicit, human-readable rules for token selection, unlike learned models which operate as black boxes.

### Efficiency

Static methods eliminate the need for model inference during token selection, offering significant speedup in production scenarios.

### Limitations

- Reliance on external NLP tools (spaCy, KenLM)
- Potential domain shift for non-English text
- Fixed window size for semantic density may not capture all contexts

## Future Work

- Extend to multilingual datasets
- Explore adaptive window sizes for semantic density
- Integrate dynamic heuristics that adjust based on document structure

## References

1. "Full Attention Strikes Back" - RTPurbo paper
2. RULER dataset documentation
3. spaCy and KenLM technical reports

## Appendix

### Configuration Files

- `data/config/rtpurbo_params.yaml`: RTPurbo hyperparameters
- `data/config/threshold.yaml`: Falsifiability threshold
- `data/config/streaming_params.yaml`: Streaming chunk configuration

### Output Files

- `data/intermediate/merged_dataset.csv`: Combined ground truth and features
- `data/results/final_report.md`: Complete evaluation report
- `data/results/statistical_report.txt`: Statistical analysis details
- `data/results/reproducibility_manifest.json`: Run metadata and versions

### Logs

- `data/logs/anomalies.csv`: Excluded documents
- `data/logs/compute_errors.log`: Feature computation errors
- `data/logs/structure_verification.txt`: Directory structure verification