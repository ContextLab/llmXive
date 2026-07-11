# Research: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

## 1. Dataset Strategy

### Verified Datasets
The project relies exclusively on the **arXiv** dataset hosted on HuggingFace Datasets. This dataset contains metadata and abstracts for scientific papers.

- **Source Name**: arXiv
- **Verified URL**: `
- **Loader**: `datasets.load_dataset("arXiv")`
- **Relevant Fields**: `abstract` (text), `authors` (list of strings), `categories` (list of strings).
- **Verification Status**: The dataset is publicly available, format-verified (JSON/Parquet), and accessible via the standard `datasets` library on CPU.

### Dataset Selection Rationale
The arXiv dataset is selected because:
1. It contains the specific categories required by the spec: `cs.CL` (Computation and Language), `physics.gen-ph` (General Physics), and `q-bio.QM` (Quantitative Methods).
2. It provides an `authors` list where the **first element** (`authors[0]`) is conventionally the lead author. The plan extracts this string for author disambiguation (FR-009).
3. Abstracts are standardized in length and structure, making them suitable for stylometric analysis where content variation is minimized compared to full texts.
4. It is accessible without GPU acceleration and fits within the memory constraints of the GitHub Actions runner when filtered.

**Dataset Variable Fit**:
- **Required Variable**: `lead_author` (String). **Status**: Derived from `authors[0]`.
- **Required Variable**: `abstract` (Text). **Status**: Present.
- **Required Variable**: `categories` (List of strings). **Status**: Present.
- **Constraint Check**: The dataset must contain at least 20 authors with ≥10 abstracts in the specified categories.

### Data Processing Plan
1. **Ingestion**: Load the full `arXiv` dataset.
2. **Filtering**:
 - Keep rows where `categories` contains any of `['cs.CL', 'physics.gen-ph', 'q-bio.QM']`.
 - **Fallback Strategy**: If < 20 eligible authors are found, expand categories to include `['cs.AI', 'stat.ML']` to ensure sufficient sample size while maintaining scientific abstract constraints.
 - Group by `lead_author` (derived as `authors[0]`).
 - Filter groups to retain only authors with `count >= 10`.
 - **Selection**: Perform **stratified random sampling** from the pool of eligible authors to select exactly 20. This prevents selection bias where "top 20" might correlate with publication volume or sub-field dominance rather than individual style.
 - *Edge Case Handling*: If < 20 authors meet the criteria even with fallback, raise a `DataInsufficientError` and log the available count.
3. **Splitting**: For each selected author, randomly split their abstracts into [deferred] training and [deferred] testing (stratified by author, though here it's per-author split).
4. **Preprocessing**:
 - Lowercase text.
 - Remove punctuation (keep alphanumeric and whitespace).
 - Tokenize into character sequences (no word tokens).
 - Exclude abstracts shorter than `n` characters (where `n=6` is the max order).

## 2. Methodology & Statistical Rigor

### N-gram Model Training (FR-003, FR-011)
- **Model Type**: Character-level N-gram Language Model.
- **Orders**: $n \in \{4, 5, 6\}$.
- **Smoothing**: **Kneser-Ney Smoothing** (Modified) is mandatory.
 - *Rationale*: With only ~10 abstracts per author, the vocabulary of character n-grams is sparse. Standard MLE would assign zero probability to unseen n-grams, causing infinite perplexity. Kneser-Ney handles sparsity by discounting counts of seen n-grams and distributing probability mass to unseen ones based on continuation counts.
 - *Sparsity Check*: Before finalizing n=6, the system will calculate the "continuation count coverage". If <80% of observed n-grams have valid continuation counts, the model will automatically downgrade to n=5 for that author and log a warning. This prevents training on noise.
 - *Implementation*: Use `scikit-learn`'s `CountVectorizer` with `ngram_range=(n, n)` and `analyzer='char'` combined with a custom smoothing wrapper, or a dedicated library like `kenlm` (if available in CPU wheels) or a pure Python implementation of Kneser-Ney to ensure no external binary dependencies fail on CI. *Decision*: A pure Python/Kneser-Ney implementation using `scikit-learn` counts is preferred for maximum portability on CPU-only runners.
- **Training Split**: 80/20.
- **Perplexity Calculation**:
 - $PP(W) = \exp\left(-\frac{1}{N} \sum_{i=1}^{N} \log P(w_i | w_{i-n+1}, \dots, w_{i-1})\right)$
 - Computed on the [deferred] held-out test set for each author.

### Cross-Evaluation & Classification (FR-004, FR-005)
- **Perplexity Matrix**: A square matrix where $M_{ij}$ is the average perplexity of Author $i$'s test set under Author $j$'s model.
- **Classification Rule**: For a test abstract $t$ from Author $i$, the predicted author $\hat{y}$ is the model $j$ that minimizes $PP(t | Model_j)$.
- **Accuracy Metric**: $\frac{\text{Count}(\hat{y} == \text{True Author})}{\text{Total Test Samples}}$.
- **Baseline Comparison**:
 - **Baseline Model**: Naive Bayes classifier trained on function-word frequencies.
 - **Function Words**: Standard English list (e.g., "the", "and", "of", "to", "a", "in", "is", "that", "for", "with").
 - **Comparison**: McNemar's test on the paired binary outcomes (correct/incorrect) of the N-gram model vs. the Baseline.

### Statistical Validation (FR-010, SC-002, SC-005)
- **Pre-registration of Primary Model**: To avoid "Best-Performer" selection bias (where selecting the best of n=4,5,6 inflates Type I error), **n=5** is pre-registered as the **primary model** for the McNemar test. Orders 4 and 6 are reported only as sensitivity analyses.
- **Multiple Comparisons**: Since we test three n-gram orders for sensitivity, we report raw p-values for all. However, the **primary hypothesis** (n=5 vs Baseline) is tested at $\alpha = 0.05$ without Bonferroni correction, as it is a single pre-registered test. If sensitivity analyses are performed, Bonferroni correction ($\alpha' = 0.05/3$) is applied.
- **Power Analysis & Limitations**:
 - *Sample Size*: ~10 test abstracts per author $\times$ 20 authors = 200 test samples.
 - *Limitation*: This sample size provides low power to detect small effect sizes (Cohen's $h \approx 0.2$). It is, however, sufficient to detect large effect sizes (Cohen's $h \approx 0.8$) with power > 0.80.
 - *Justification*: Given the constraints of the dataset (only 20 authors with $\ge$ 10 abstracts), this is the maximum feasible sample size. The study is framed as a "proof of concept" for stylometric signals in technical writing.
 - *Interpretation*: A non-significant result will be interpreted as "inconclusive due to low power" rather than "null effect".
- **Collinearity**: Not applicable in the standard sense as predictors are character sequences, but the dependency of n-grams (order $n$ contains order $n-1$) is handled by the smoothing algorithm and the separate evaluation of each order.

### Robustness Check (FR-007, SC-003)
- **Hybrid Generation**: Create synthetic abstracts by:
 1. **Author Swap**: Swapping the *first* and *last* sentences between two authors (maximizing structural disruption).
 2. **Random Swap Control**: Swapping the *first* and *last* sentences of an abstract with sentences from the *same* author (to control for sentence-level coherence vs. authorial style).
- **Metric**: Compare classification accuracy on:
 1. Original abstracts.
 2. Author-swapped hybrids.
 3. Random-swapped hybrids.
- **Expectation**: The drop in accuracy for **Author-swapped** hybrids should be **significantly larger** than for **Random-swapped** hybrids. This distinguishes true authorial style (which degrades when mixed) from general syntactic templates (which remain stable in random swaps).

## 3. Compute Feasibility & Resource Management

### Hardware Constraints
- **Runner**: GitHub Actions Free Tier (multiple CPU cores, 7 GB RAM, 14 GB Disk).
- **No GPU**: All operations must be CPU-based.

### Optimization Strategy
1. **Data Subsetting**: The dataset is filtered *before* loading into memory. Only a selected subset of top authors (representing a substantial volume of abstracts) are kept. This reduces memory footprint from GBs to MBs.
2. **N-gram Order**: $n \le 6$. The state space for character n-grams (alphabet ~26 + space + digits) grows as $27^6 \approx 387M$, but with only ~500 abstracts, the actual observed n-grams will be sparse.
3. **Memory Management**:
 - Use `datasets` streaming or map with `num_proc=1` to avoid forking overhead.
 - Process authors sequentially in the training loop to avoid holding 20 large models in memory simultaneously.
 - Clear memory (`del` and `gc.collect()`) between author model trains.
4. **Time Budget**:
 - Training 20 authors $\times$ 3 orders = 60 models.
 - **Revised Target**: [deferred] per author (total [deferred] for training) using optimized vectorization. The previous 300s estimate was overly conservative for n-gram models.
 - Evaluation: Fast lookup.
 - Total estimated runtime: < 1.5 hours.

### Risk Mitigation
- **Risk**: Memory overflow during Kneser-Ney smoothing calculation.
 - *Mitigation*: Use a sparse matrix representation for n-gram counts. If memory spikes, reduce the max n-gram order to 4 or 5 dynamically and log a warning.
- **Risk**: Dataset download failure.
 - *Mitigation*: Implement retry logic with exponential backoff. Cache the dataset locally in `data/raw/` if the runner allows (GitHub Actions caches).

## 4. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| **Kneser-Ney Smoothing** | Essential for data sparsity with ~10 abstracts/author. | MLE (infinite perplexity), Laplace (over-smoothing). |
| **Pre-registered n=5** | Avoids selection bias from "best-of-three" testing. | Testing all orders and picking the best (inflates Type I error). |
| **Stratified Random Sampling** | Controls for publication volume bias. | Selecting "top 20" by count (confounds style with productivity). |
| **Hybrid Control (Random Swap)** | Distinguishes authorial style from syntactic templates. | Single author-swap only (ambiguous signal source). |
| **Function-Word Baseline** | Standard baseline for stylometry; tests if character patterns add value beyond common words. | Random baseline (too easy to beat), Topic-model baseline (too complex, not in spec). |
| **Fallback Categories** | Ensures research question is answerable if primary categories are sparse. | Halting execution (research dead-end). |