# Research Context: Middle-Third Bias in VLMs

## Problem Statement

Visual Language Models (VLMs) exhibit a "middle-third" bias where accuracy drops significantly for questions targeting the middle section of long documents compared to the first or last thirds.

## Hypothesis

Decoupled retrieval mechanisms can mitigate this bias by explicitly injecting relevant context from the middle section into the VLM's input, bypassing the attention decay inherent in long-context processing.

## Methodology

1. **Synthetic Data Generation**: Create documents with controlled text density and layout.
2. **Baseline Evaluation**: Measure accuracy on static images without retrieval.
3. **Retrieval Evaluation**: Measure accuracy with retrieved snippets injected.
4. **Correlation Analysis**: Correlate recovery magnitude with model context window size.

## Metrics

- **Positional Accuracy**: Accuracy per third (first, middle, last).
- **Bias Delta**: Difference between middle-third accuracy and average of first/last.
- **Recovery Delta**: Improvement in middle-third accuracy with retrieval vs. baseline.
- **Correlation Coefficient**: Spearman's rho between recovery delta and context window size.
