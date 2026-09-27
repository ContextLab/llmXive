# Research: Zero-Shot Drift Detection for AgentDoG 1.5

## Overview
This research validates the feasibility of using centroid embeddings for zero-shot drift detection within the strict resource constraints of a GitHub Actions free-tier runner (GB RAM, 2 CPU cores). It confirms the availability of the required datasets and models and outlines the statistical methodology.

## Verified Datasets

The following datasets are verified as open, directly downloadable, and suitable for the AgentDoG 1.5 taxonomy validation. Note: A perfect "AgentDoG" dataset is not publicly available. We use a **Safety-Proxy** strategy for methodological testing only. The final validation requires a human-annotated dataset, but a publicly available source is currently lacking.

| Dataset Name | Source | Verified URL | Notes |
| :--- | :--- | :--- | :--- |
| **All-MiniLM-L6-v2** | Hugging Face | `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2` | CPU-friendly embedding model (low memory footprint). |
| **google/flan-t5-small** | Hugging Face | `https://huggingface.co/google/flan-t5-small` | Baseline model. Moderate RAM usage. Fits within the 7GB budget. |

*Note: The "Safety-Proxy" datasets are used to test the *methodology* of drift detection. The "Novel" ground truth is defined by human annotators on this proxy data. A verified public source for the human-annotated dataset is currently unavailable.*

## Dataset Strategy

| Component | Strategy | Source |
| :--- | :--- | :--- |
| **Input Logs** | Stream from Hugging Face `datasets` library (bigcode/the-stack subset). | Verified HF Dataset |
| **Centroids** | Compute mean embedding of labeled examples per category. | Derived from Input |
| **Human Annotations** | Ingested from `data/human_annotations.json` (external input). | External (Manual) - **no public source** |
| **Novelty Ground Truth** | Defined by human annotators as patterns *outside* the scope of the 4 safety categories. | Human-Defined |

## Model & Methodology

### Embedding Generation
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`.
- **Rationale**: Specifically chosen for its small footprint (~80MB) and high performance on semantic similarity tasks. It runs efficiently on CPU.
- **Batch Size**: 64 (Verified Fact: `2410.21676`).

### Drift Scoring
- **Method**: Cosine Distance.
- **Formula**: $D = 1 - \frac{A \cdot B}{||A|| ||B||}$
- **Centroids**: For each safety category $C$, compute $Centroid_C = \frac{1}{N} \sum_{i=1}^{N} Embedding(log_i)$ where $log_i \in C$.
- **Drift Score**: $Score = \min_{C} (Distance(Embedding(log), Centroid_C))$.

### Baseline Comparison
- **Model**: `google/flan-t5-small`.
- **Task**: Zero-shot classification of "Is this log novel/harmful?" (Specific prompt: "Is this text a novel safety threat not covered by standard categories?").
- **Constraint**: Runs on CPU. If memory error occurs, fallback to `google/flan-t5-small` quantized or a smaller variant.
- **AUC Calculation**: The AUC-ROC is calculated against the **human-labeled "Novel"** (1/0), not against the model's own output.

### Statistical Validation
- **US-01 (Drift Separation)**:
  - Test: Mann-Whitney U test between **Human-Labeled Novel** and **Human-Labeled Benign** groups.
  - Metric: Cohen's d (Effect size).
  - Significance: $p < 0.05$.
- **US-02 (Human Agreement)**:
  - Metric: Cohen's Kappa ($\kappa$) for agreement between System Flag and Human Label.
  - Method: Logistic regression is used separately to estimate the odds ratio of a log being labeled "Novel" given its drift score.
- **US-03 (Baseline)**:
  - Metric: AUC-ROC.
  - Threshold: Drift AUC $\ge$ (Flan-T5 AUC - 0.10).

## Compute Feasibility Analysis

- **RAM**:
  - `all-MiniLM-L6-v2`: ~80MB.
  - `google/flan-t5-small`: ~300MB.
  - Data (Streaming): < 500MB overhead.
  - Context/Activation: A conservative estimate of approximately 3-4 GB for 10k logs with batch size 64.
  - **Total**: < 5GB. Well within 7GB limit.
- **CPU**:
  - Embedding a large-scale set of logs @ a moderate batch size: ~15-20 minutes on 2 cores.
  - Flan-T5 Inference: **4-6 hours** (conservative estimate for 10k logs on 2-core CPU).
  - **Total**: < 6 hours. Within 6-hour limit.
- **GPU**: Not required. The plan explicitly avoids GPU dependencies.

## Decision Rationale

The choice of `all-MiniLM-L6-v2` and `google/flan-t5-small` is driven by the strict **CPU-first** requirement. These models are the smallest viable options that maintain semantic fidelity. The decision to **exclude** a GPU escape hatch is a direct response to Constitution Principle VII, ensuring the project remains reproducible on the free-tier runner without external dependencies. The **strict human validation gate** ensures that the "Zero-Shot Drift Validity" is not merely a theoretical exercise but a verified empirical result. The **Safety-Proxy** dataset strategy acknowledges the lack of a perfect public dataset while allowing for methodological validation.
