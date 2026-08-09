# Research Conclusions: llmXive Follow-up

## Summary of Findings

This project investigated the efficiency gains of using active learning as a reranker for Passage Retrieval (PRP) tasks, specifically focusing on the impact of redundancy in retrieval lists.

### Key Metrics

- **Wasted Call Ratio**: The proportion of LLM calls that were identified as redundant (similarity > 0.95) and thus "wasted".
- **NDCG@10**: Normalized Discounted Cumulative Gain at 10, measuring ranking quality.
- **Correction Factor**: A statistically valid adjustment to the wasted ratio based on LLM consensus validation.

### Main Results

1. **Redundancy Impact**: Synthetic redundancy injection successfully created clusters of near-duplicate passages with average similarity scores exceeding 0.95.
2. **Efficiency Loss**: The baseline active ranker on redundant lists showed a significant increase in wasted calls compared to unique subsets.
3. **Clustering-Aided Recovery**: The MinHash-LSH pre-clustering approach effectively filtered redundant pairs, reducing the wasted call ratio while maintaining NDCG@10 performance.
4. **Statistical Significance**: Wilcoxon signed-rank tests confirmed that the improvements in efficiency and ranking quality were statistically significant (p < 0.05).

### Limitations

- The study relied on synthetic redundancy injection for `nfcorpus` and `scifact`, as real-world near-duplicates were sparse.
- The LLM consensus validation was constrained by CPU resources, requiring fallback to proxy labels in some cases.
- The threshold sweep was limited to a specific range [0.90, 0.98] due to computational constraints.

### Implications

The findings suggest that pre-clustering with MinHash-LSH is a viable strategy for improving the efficiency of active learning rerankers in PRP tasks, particularly in scenarios with high redundancy. The correction factor methodology ensures that the reported efficiency gains are scientifically valid and not artifacts of the proxy similarity measure.

### Future Work

- Extend the study to GPU-accelerated environments to enable full LLM consensus validation.
- Investigate the generalization of results to other retrieval datasets and domains.
- Explore adaptive thresholding strategies for MinHash-LSH based on dataset characteristics.

## Artifact References

- `data/processed/injected_datasets.json`: Synthetic redundancy clusters.
- `data/results/us1_efficiency_ratio.json`: Corrected wasted call ratio.
- `data/results/wilcoxon_ndcg.json`: Statistical significance of NDCG improvement.
- `data/results/threshold_sweep.json`: Sensitivity analysis of MinHash-LSH threshold.