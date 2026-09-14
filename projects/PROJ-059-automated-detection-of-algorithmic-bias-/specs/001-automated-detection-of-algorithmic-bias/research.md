# Research: Automated Detection of Algorithmic Bias in Public Code Repositories

## Dataset Strategy

| Dataset Name | URL | Purpose | Variables Used | Data Volume |
|---|---|---|---|---|
| VADER Sentiment Lexicon | https://huggingface.co/datasets/bartoszmaj/vader_sentiment_full/resolve/main/data/train-00000-of-00001-16eab957b5f41fe3.parquet | Sentiment analysis of code comments | Sentiment scores | ~10MB |
| VADER Speak | https://huggingface.co/datasets/samdotme/vader-speak/resolve/main/data/train-00000-of-00001.parquet | Alternative sentiment analysis lexicon | Sentiment scores | ~10MB |
| VADER Speak Video | https://huggingface.co/datasets/samdotme/vader-speak-video/resolve/main/data/train-00000-of-00001.parquet | Alternative sentiment analysis lexicon | Sentiment scores | ~10MB |

## Decision/Rationale

All methods will be implemented to run on the CPU. VADER sentiment analysis and statistical calculations (Spearman correlation, Bonferroni correction) are computationally feasible on the provided hardware. Synthetic data generation is also CPU-bound. No GPU acceleration is required.

## Background Research

*   **Static Code Analysis**: The `ast` module in Python provides a robust way to parse Python code and extract relevant information, such as variable names and comments.
*   **Sentiment Analysis**: VADER (Valence Aware Dictionary and sEntiment Reasoner) is a lexicon and rule-based sentiment analysis tool that is well-suited for analyzing short text snippets like code comments.
*   **Fairness Metrics**: Demographic Parity and Equalized Odds are widely used fairness metrics that measure the difference in outcomes between different groups.
*   **Statistical Correlation**: Spearman's rank correlation is a non-parametric measure of association that is suitable for analyzing the relationship between ranked variables.

## Experiment Design

The core experiment will involve the following steps:

1.  **Data Extraction**: Extract variable names and comments from a set of Python repositories using the `ast` module.
2.  **Textual Feature Engineering**: Tokenize the extracted text and calculate a "Textual Bias Score" based on the frequency of matched terms from the demographic lexicon and sentiment scores from VADER.
3.  **Synthetic Data Generation**: Generate synthetic data with controlled class imbalances and inject bias using a controlled `injected_skew_magnitude` parameter.
4.  **Fairness Metric Calculation**: Calculate Demographic Parity and Equalized Odds on the synthetic data.
5.  **Correlation Analysis**: Compute Spearman's rank correlation between the Textual Bias Scores and the Fairness Metrics.
6.  **Statistical Validation**: Apply Bonferroni correction to account for multiple comparisons.

## Key Risks

*   **Data Availability**: Ensuring access to a sufficient number of public Python repositories.
*   **Data Quality**: The accuracy of the VADER sentiment analysis and the relevance of the demographic lexicon.
*   **Statistical Power**: The sample size may be insufficient to detect a statistically significant correlation.
*   **Computational Resources**: The limited compute resources may restrict the scalability of the analysis.
