---
field: computer science
submitter: google.gemma-3-27b-it
---

# Automated Detection of Algorithmic Bias in Public Code Repositories

**Field**: Computer Science

## Research question

To what extent do variable naming conventions and developer comments in open-source Python projects correlate with downstream algorithmic fairness metrics computed on independently generated, domain-neutral synthetic datasets, serving as reliable early signals of biased design choices?

## Motivation

Algorithmic bias often originates in design decisions made long before model training, embedded in the semantic choices of developers. While current fairness auditing focuses on trained model outputs, there is a critical gap in understanding if "soft" signals in source code—such as gendered variable names or biased sentiment in comments—act as predictive indicators of downstream unfairness. Identifying these early signals could enable lightweight, pre-deployment audits that prevent bias propagation at the source.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using the following distinct queries:
1. "algorithmic bias detection source code variable names"
2. "textual artifacts bias software repositories"
3. "correlation code comments algorithmic fairness metrics"
We also broadened the search to include "fairness testing software" and "ML bias in code" to capture tangential methodological work.

### What is known
- [Fairness Testing: Testing Software for Discrimination (2017)](https://arxiv.org/abs/1709.03221) — Defines software fairness and discrimination and develops a testing-based method for measuring discrimination, focusing on causality in discriminatory behavior, but does not link these metrics to source code text artifacts.
- [Fairway: A Way to Build Fair ML Software (2020)](https://arxiv.org/abs/2003.10354) — Proposes a framework for building fair ML software and discusses bias in the learned model, but does not investigate source code comments or variable naming as predictors of bias.
- [BotHawk: An Approach for Bots Detection in Open Source Software Projects (2023)](https://arxiv.org/abs/2307.13386) — Focuses on detecting automated bots in OSS collaboration; while it analyzes repository metadata, it offers no analysis of textual artifacts as predictors of algorithmic fairness.

### What is NOT known
There is currently no published empirical evidence linking specific textual patterns in source code (variable names, comments) to quantitative downstream fairness metrics (e.g., demographic parity, equalized odds). Existing literature treats code analysis and fairness auditing as separate domains, with no study attempting to bridge them by using NLP on code as a proxy for model bias.

### Why this gap matters
Bridging this gap matters because it could shift bias mitigation from a post-hoc, computationally expensive model audit to a lightweight, static analysis step. If valid, this would allow maintainers of large open-source projects to flag potential bias issues immediately during code review, significantly reducing the cost and latency of fairness interventions.

### How this project addresses the gap
This project directly addresses the gap by constructing a dataset of Python repositories where both the textual artifacts (names/comments) and the downstream algorithmic behavior (simulated or extracted fairness metrics) are measured. By correlating these two distinct data sources, we will determine if textual artifacts possess statistical predictive power for bias, effectively testing the hypothesis that source code semantics are a leading indicator of algorithmic fairness.

## Expected results

We expect to find a statistically significant, albeit moderate, correlation between specific "biased" naming patterns (e.g., gendered terms in variable names related to people) and lower fairness scores in the associated algorithms. We anticipate that a simple NLP-based scoring system will achieve a precision of >0.6 in flagging high-risk code segments, with false positives primarily driven by domain-specific terminology that mimics bias patterns.

## Methodology sketch

- **Data Collection**: Use the GitHub API to download 500-1,000 public Python repositories from domains known for fairness sensitivity (e.g., finance, hiring, criminal justice) using the `requests` library, ensuring total repository size fits within 7GB RAM limits.
- **Static Analysis**: Parse source files using Python's `ast` module to extract all variable names, function names, and string literals (comments) without executing code.
- **Textual Feature Extraction**:
  - Tokenize variable names (handling camelCase/snake_case) and match against a curated lexicon of demographic-coded terms.
  - Apply VADER sentiment analysis to comments to detect negative or stereotyping sentiment.
- **Ground Truth Construction**:
  - Identify algorithmic modules within the code (e.g., sorting, scoring functions).
  - **Crucial Independence Step**: Generate synthetic input data using domain-neutral distributions (e.g., uniform or Gaussian) from `numpy` that mimic the repository's domain structure but contain no actual sensitive attributes or historical bias, ensuring the data is strictly independent of the code's textual features.
  - Execute the extracted logic on this synthetic data to compute standard fairness metrics (Demographic Parity, Equalized Odds) using `AIF360` or `Fairlearn` libraries.
- **Correlation Analysis**:
  - Compute a "Textual Bias Score" for each file based on naming and comment features.
  - Correlate these scores with the computed downstream fairness metrics using Pearson correlation and chi-square tests.
- **Validation**: Ensure the validation target (fairness metrics on synthetic data) is strictly independent of the predictor (textual features) by verifying the synthetic data generation process does not ingest or reference the code's variable names or comments.
- **Scope Check**: Limit dataset size and complexity to ensure the entire pipeline (download, parse, analyze, test) runs within 6 hours on 2 CPU cores with <7GB RAM, avoiding heavy deep learning models in favor of static analysis and lightweight NLP.

## Duplicate-check

- Reviewed existing ideas: Automated Detection of Algorithmic Bias in Public Code Repositories
- Closest match: None in current corpus (first iteration of this idea)
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-11T06:58:55Z
**Outcome**: exhausted
**Original term**: Automated Detection of Algorithmic Bias in Public Code Repositories computer science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Automated Detection of Algorithmic Bias in Public Code Repositories computer science | 0 |
| 1 | algorithmic fairness in open-source software | 5 |
| 2 | bias detection in machine learning code repositories | 0 |
| 3 | automated auditing of software for discriminatory logic | 0 |
| 4 | fairness-aware code analysis tools | 0 |
| 5 | detecting algorithmic discrimination in GitHub projects | 0 |
| 6 | bias in open-source machine learning libraries | 0 |
| 7 | fairness metrics for software code review | 0 |
| 8 | algorithmic transparency in public codebases | 0 |
| 9 | identifying bias in data science code repositories | 0 |
| 10 | fairness-aware static analysis for software | 0 |
| 11 | bias detection in neural network implementations | 0 |
| 12 | equitable algorithm detection in software engineering | 0 |
| 13 | automated fairness testing for code repositories | 0 |
| 14 | bias in open-source AI model code | 0 |
| 15 | detecting unfairness in software algorithms | 0 |
| 16 | algorithmic accountability in public code | 0 |
| 17 | fairness evaluation of open-source software | 0 |
| 18 | bias in software development lifecycle | 0 |
| 19 | automated detection of unfair code patterns | 0 |
| 20 | algorithmic bias in software supply chains | 0 |

### Verified citations

1. **BotHawk: An Approach for Bots Detection in Open Source Software Projects** (2023). Fenglin Bi, Zhiwei Zhu, Wei Wang, Xiaoya Xia, Hassan Ali Khan, et al.. arXiv. [2307.13386](https://arxiv.org/abs/2307.13386). PDF-sampled: No.
2. **Fairway: A Way to Build Fair ML Software** (2020). Joymallya Chakraborty, Suvodeep Majumder, Zhe Yu, Tim Menzies. arXiv. [2003.10354](https://arxiv.org/abs/2003.10354). PDF-sampled: No.
3. **Fairness Testing: Testing Software for Discrimination** (2017). Sainyam Galhotra, Yuriy Brun, Alexandra Meliou. arXiv. [1709.03221](https://arxiv.org/abs/1709.03221). PDF-sampled: No.
