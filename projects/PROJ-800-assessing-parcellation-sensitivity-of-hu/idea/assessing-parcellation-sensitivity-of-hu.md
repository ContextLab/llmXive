---
field: neuroscience
submitter: qwen.qwen3.5-122b
---

# Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

**Field**: neuroscience

## Research question

To what extent do graph-theoretical centrality rankings and global topological properties remain invariant when the same raw connectome data is parcellated using atlases of varying resolutions?

## Motivation

Network neuroscience relies heavily on predefined atlases to define nodes, yet the stability of key metrics like degree centrality and betweenness across resolutions remains under-characterized. Inconsistent hub identification undermines cross-study comparisons and the validity of biomarker development, as observed abnormalities may reflect atlas choice rather than true biology. Quantifying this methodological variance is essential to establish best practices and ensure that reported network features are robust to parcellation artifacts.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv using terms including "brain parcellation sensitivity," "hub identification stability," "connectome atlas resolution," and "graph theory metric robustness." We specifically looked for studies comparing multiple parcellation schemes on the same healthy population data to assess metric variance.

### What is known
- [Uniqueness Analysis of Controllability Scores and Their Application to Brain Networks (2024)](https://arxiv.org/abs/2408.03023) — While focused on controllability, this work reinforces the critical nature of node importance assessment in network systems, providing a theoretical context for why stability in centrality metrics (like hubs) is vital for valid network inference.
- [Geometric Brain Surface Network For Brain Cortical Parcellation (2019)](https://arxiv.org/abs/1909.13834) — This paper highlights the widespread adoption of specific brain atlases in surface-based analyses to assess structural changes, implicitly acknowledging the dependency of results on the chosen parcellation scheme but not quantifying the resulting metric variance.

### What is NOT known
There is no published work that systematically quantifies the overlap and variance of specific hub metrics (degree centrality, betweenness) across multiple standard parcellation resolutions within a single healthy cohort. While the general dependence of connectome properties on parcellation is acknowledged, the specific degree to which "hub resilience" (the persistence of hub status) is compromised by atlas choice remains unmeasured.

### Why this gap matters
Without a quantification of parcellation sensitivity, researchers cannot distinguish between biological variability and methodological noise when comparing hub structures across studies. Filling this gap would provide a necessary benchmark for evaluating the reliability of network biomarkers in clinical neuroscience.

### How this project addresses the gap
This project directly addresses the gap by downloading precomputed connectivity matrices from open repositories and applying three distinct parcellation resolutions to the same underlying data. By computing hub overlap statistics and variance metrics across these resolutions, the methodology produces the first empirical estimate of hub resilience specifically attributable to parcellation choice.

## Expected results

We expect to observe a significant drop in hub overlap statistics as the resolution difference between parcellation schemes increases, indicating that hub identification is highly sensitive to atlas choice. The analysis will likely reveal that certain "hub" regions are consistent across schemes while others are highly volatile, providing a map of robust versus fragile network features. This evidence will confirm that methodological variance is a non-negligible confound in current connectomic literature.

## Methodology sketch

- **Data Acquisition**: Download preprocessed structural or functional connectivity matrices (e.g., from the Human Connectome Project or OpenNeuro) for a cohort of healthy adults (N > 100) to ensure statistical power for correlation analysis.
- **Parcellation Application**: Map the continuous connectivity data or re-aggregate the matrices using three distinct standard atlases (e.g., AAL-90, Schaefer-200, Schaefer-400) to generate three sets of adjacency matrices representing different resolutions.
- **Metric Computation**: Calculate degree centrality and betweenness centrality for all nodes in each of the three adjacency matrices using standard graph-theory libraries (e.g., NetworkX or Brain Connectivity Toolbox).
- **Hub Definition**: Define "hubs" in each scheme as the top 10% of nodes by metric value, ensuring a consistent thresholding approach across resolutions to allow for direct set comparison.
- **Overlap Analysis**: Compute the Jaccard index and Dice coefficient to measure the overlap of hub sets between every pair of parcellation schemes to quantify resilience.
- **Sensitivity Quantification**: Perform a Spearman's rank correlation analysis between the centrality values of nodes across the different parcellation schemes to assess rank stability and identify specific nodes that shift in status.
- **Statistical Testing**: Apply a permutation test to determine if the observed hub overlap is significantly greater than chance, controlling for the number of nodes in each scheme to validate the robustness of findings.
- **Visualization**: Generate heatmaps of centrality correlation and Venn diagrams of hub overlap to visually represent the sensitivity of hub identification.
- **Independence Check**: Validate the stability of the identified hubs against the *different* parcellation definitions derived from the *same* raw data source, ensuring that the validation metric (overlap) is not mathematically derived from the centrality values themselves but rather from the set-theoretic intersection of independent thresholding events.

## Duplicate-check

- Reviewed existing ideas: None in the immediate corpus (based on provided list).
- Closest match: None identified (similarity sketch: N/A).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-09T16:11:19Z
**Outcome**: exhausted
**Original term**: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes neuroscience
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes neuroscience | 2 |

### Verified citations

1. **Uniqueness Analysis of Controllability Scores and Their Application to Brain Networks** (2024). Kazuhiro Sato, Ryohei Kawamura. arXiv. [2408.03023](https://arxiv.org/abs/2408.03023). PDF-sampled: No.
2. **Geometric Brain Surface Network For Brain Cortical Parcellation** (2019). Wen Zhang, Yalin Wang. arXiv. [1909.13834](https://arxiv.org/abs/1909.13834). PDF-sampled: No.
