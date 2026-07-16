# Research: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

## Problem Statement

The "alignment gap" in text-to-image models refers to the discrepancy between automated metrics (like CLIP score) and human judgment. This project investigates whether specific linguistic features of the input caption (semantic surprisal, syntactic complexity, length) can predict this deviation. The hypothesis is that captions with higher complexity or ambiguity lead to larger alignment gaps, suggesting that current metrics fail more often on linguistically challenging inputs.

## Dataset Strategy

The analysis relies on the **Pick-a-Pic** dataset, which contains explicit human preference ratings (winner/loser pairs) for image-caption pairs. This dataset is verified to contain the necessary `human_rating` proxy (derived from preference pairs) to calculate the "Deviation Score" ($| \text{CLIP\_Score} - \text{Human\_Rating} |$) without circularity.

### Verified Datasets

The following datasets are verified for availability and format. We will use Pick-a-Pic for human ratings and compute CLIP scores on the fly.

| Dataset Name | Purpose | Verified URL / Source | Access Method |
|:--- |:--- |:--- |:--- |
| **Pick-a-Pic** | Source of human preference ratings (winner/loser) for captions. | `https://huggingface.co/datasets/pick-a-pic/pick-a-pic/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset(..., streaming=True)` |
| **BERT Base** | Pre-trained BERT model for perplexity calculation. | ` (Model Hub) | Loaded via `transformers` for inference |
| **COCO Images** | (Optional) Image source if Pick-a-Pic lacks images, otherwise use Pick-a-Pic images. | ` | Streaming if needed |

*Note: The "COCO Captions" dataset was considered but rejected as the primary source for the target variable because it lacks explicit human preference ratings for every caption. Using a CLIP-consensus proxy was rejected due to circular dependency concerns.*

**Data Availability Assessment**:
- **Open Access**: Yes. Pick-a-Pic is public on Hugging Face.
- **Download Feasibility**: The Pick-a-Pic dataset is large. We will use `streaming=True` to process data in chunks, avoiding the need to download the full dataset into RAM.
- **Variable Fit**: The Pick-a-Pic dataset contains the `prompt` (caption), `image` (optional but usable for CLIP), and `winner`/`loser` fields.
 - *Target Construction*: We will derive `human_rating` from the preference pairs. If a caption was the "winner" in a pair, it gets a higher score; if "loser", a lower score. We will normalize these to [0, 1].
 - *Covariates*: We will calculate `caption_length` and `image_complexity` (if images are available) to control for confounding variables.

## Methodology

### 1. Feature Extraction (FR-001, FR-002)
- **Semantic Surprisal**: Computed as $\ln(\text{Perplexity})$ using a pre-trained BERT model. *Note: This is an operational proxy for "semantic uncertainty" and differs from the strict "Semantic Entropy" of generative models (Farquhar et al., 2024).*
- **Syntactic Complexity**: Maximum depth of the dependency parse tree using `spaCy`.
- **Noun-Phrase Density**: Ratio of noun phrases to total tokens.
- **Token Diversity**: Unique tokens / total tokens.
- **Covariates**: `caption_length` (token count) and `image_complexity` (if available).
- **Implementation**: Run on CPU. Batch processing to maximize throughput.

### 2. Target Variable Calculation (FR-003)
- Normalize CLIP scores and Human Ratings (derived from Pick-a-Pic preferences) to $[0, 1]$.
- Compute $Y = | \text{CLIP\_Score} - \text{Human\_Rating} |$.
- Exclude rows with missing ratings or invalid pairs.

### 3. Model Training (FR-004, FR-005)
- **Algorithm**: XGBoost (Gradient Boosted Trees).
- **Hardware**: CPU only.
- **Validation**: 5-fold cross-validation.
- **Metric**: Pearson Correlation ($r$) between predicted and actual deviation.

### 4. Statistical Significance (FR-006)
- **Permutation Test**: Shuffle labels multiple times to build a null distribution for each feature's importance.
- **Correction**: Benjamini-Hochberg procedure to control FDR at 0.05.
- **Reproducibility**: Fixed random seed (e.g., 42).

### 5. Sensitivity Analysis (SC-005)
- Re-run the training and significance test with multiple random seeds.
- Aggregate feature importance rankings to measure stability.

## Statistical Rigor & Limitations

- **Causal Inference**: This is an **observational** study. We are correlating linguistic features with deviation. We cannot claim that "complex syntax *causes* CLIP failure," only that they are associated.
- **Collinearity**: Linguistic features (e.g., entropy and complexity) may be correlated. We will report VIF (Variance Inflation Factor) and use permutation importance (which handles collinearity better than coefficients) to rank features. We explicitly control for `caption_length` to avoid spurious correlations.
- **Power**: The sample size will be limited by the CI runner's RAM (approx. tens of thousands of samples via streaming). We will report the effective sample size and acknowledge power limitations for detecting small effect sizes.
- **Multiple Comparisons**: The Benjamini-Hochberg correction (FR-006) explicitly addresses the risk of false positives when testing multiple features.

## Compute Feasibility

- **CPU-First**: BERT inference on CPU is slow but feasible for ~10k-20k samples within 6 hours if batched. XGBoost training is highly efficient on CPU.
- **Memory**: **Streaming** is the primary mechanism to ensure we never load the full dataset into RAM, satisfying the 7GB limit (Constitution Principle VII).
- **GPU Escape Hatch**: Not required. The entire pipeline is designed to run on CPU. If BERT inference becomes a bottleneck, we will use a smaller distilled BERT model (e.g., `bert-tiny`) or reduce the sample size, rather than switching to GPU.