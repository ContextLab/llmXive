# Research: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

## Problem Statement

Is explicit spatial organization of episodic memories in transformer architectures **associated** with recall accuracy on sequential memory benchmarks compared to non-spatial embedding strategies?

*Note: The study is correlational. No causal claims are made regarding the "effect" of spatial organization, as the architecture is not randomized. Findings will be framed as associations.*

## Causal Framing

This study compares two fixed architectures (spatial vs. non-spatial). Without randomization of the spatial mechanism itself (e.g., randomizing slot assignments or using a within-subject design), the analysis cannot support causal conclusions about the *effect* of spatial organization. The research question is reframed to ask about **association**.

## Literature Review & Theoretical Basis

### Spatial Memory in Cognitive Science
The "Memory Palace" (Method of Loci) relies on spatial organization to enhance episodic recall. In neuroscience, place cells in the hippocampus encode spatial coordinates, providing a framework for associative memory. This project tests whether a similar mechanism in transformers is associated with improved recall of sequential information.

### Transformer Architectures and Memory
Standard transformers use self-attention for context modeling but lack explicit spatial indexing. Recent work explores external memory modules (e.g., Neural Turing Machines), but their integration with large language models remains under-explored. This project proposes a lightweight spatial slot mechanism that assigns episodic chunks to a 2-D grid.

### Measurable Structural Correlates
Per reviewer Rosalind Franklin, the plan must include a measurable structural correlate. The **interference distance metric** serves this purpose: it measures the drop in recall accuracy when semantically unrelated items are assigned to adjacent grid coordinates. A successful spatial model should show reduced interference compared to a baseline.

## Dataset Strategy

### Verified Datasets
The following datasets are used, sourced exclusively from verified Hugging Face IDs:

| Dataset | Source ID | Purpose |
|---------|------------|---------|
| bAbI Task 3 | `facebook/babi` | Temporal reasoning targets |
| LAMBADA | `cse-lambada` | Long-context prediction targets |
| Story Cloze Test | `allenai/story_cloze` | Narrative coherence targets |

*Note: Datasets will be loaded via `datasets.load_dataset` using the verified IDs. If a dataset is unavailable, it will be skipped and the reason logged.*

### Dataset Variable Fit
- **bAbI Task 3**: Provides temporal reasoning targets (e.g., "Where is the milk?"). Matches the episodic recall outcome variable.
- **LAMBADA**: Provides long-context prediction targets. Tests the model's ability to retain information over long sequences.
- **Story Cloze**: Provides narrative coherence targets. Tests the model's ability to recall story elements in order.

*Note: While bAbI is synthetic and LAMBADA/Story Cloze are natural language, the 'exact-match recall' metric serves as a unified outcome variable valid across all three. The spatial mechanism may differentially affect synthetic positional data vs. semantic coherence. Construct validity is acknowledged as a limitation. bAbI and LAMBADA are proxies for 'episodic' memory; the 'episodic' nature is simulated via task structure.*

### Data Acquisition
Datasets will be downloaded using `datasets.load_dataset` with `streaming=True` to fit within the available disk constraints. If a dataset exceeds available RAM, the implementation will subsample (first N rows) or cap the dataset to [deferred] of the original size (FR-010).

## Methodology

### Model Architecture
- **Base Model**: `gpt2-medium` (355M parameters) loaded with 4-bit quantization (`bitsandbytes==0.41.0`).
- **Spatial Variant**: Adds a 2-D grid of 64 memory slots. Each episodic chunk is assigned a coordinate (x, y) based on a deterministic hash of its content. **Retrieval** uses cosine similarity between the current hidden state and slot embeddings, which are learned via the transformer's attention mechanism. This distinguishes the learned spatial bias from a static index.
- **Baseline Variant**: Standard `gpt2-medium` without spatial slots.

*Note: The comparison is between 'spatial-indexed external memory' and 'native attention'. The hypothesis is about the benefit of spatial indexing specifically, not just external memory. While the coordinate assignment is static, the retrieval mechanism is learned, addressing the concern that the spatial structure is external to the learning process. This is a valid comparison of architectural choices (slots vs. attention).*

### Training Protocol
- **Epochs**: 3
- **Batch Size**: 8 (reduced to 4 if peak RSS > 6.0 GB)
- **Learning Rate**: 5e-5
- **Random Seeds**: 0, 1, 2, 3, 4
- **Optimizer**: AdamW
- **Quantization**: 4-bit (CPU-compatible)

*Note: The short training window (3 epochs) is a constraint. The spatial module is initialized with a learned bias, and the 3 epochs are intended for the model to adapt its attention to the spatial slots. This may limit convergence.*

### Evaluation Metrics
- **Exact-Match Recall Accuracy**: Primary metric for FR-004.
- **Interference Distance**: Drop in recall when unrelated items are assigned to adjacent slots (FR-011).
  - *Definition*: 'Unrelated items' are identified via semantic similarity (using a pre-trained sentence transformer, threshold < 0.3). 'Adjacent' is defined as grid coordinates with Manhattan distance = 1. An adversarial test subset is constructed by injecting these items.
  - *Protocol*: (1) Identify semantically unrelated pairs (cosine similarity < 0.3); (2) Assign them to adjacent grid coordinates (Manhattan distance = 1) via a controlled injection script; (3) Measure recall drop compared to a neutral control assignment.
  - *Metric*: `Recall_drop = Accuracy_baseline - Accuracy_interference`.
  - *Note*: This metric tests the model's robustness to the hash-induced collisions, not just the hash properties. The metric measures the *drop* in recall when collisions occur, which is a valid test of the model's ability to recover from spatial interference. FIFO eviction is logged and the metric is computed on the *final* state after eviction.
- **Slot Occupancy Distribution**: Distribution of memory slots used per sample (FR-008), logged as a list of counts per slot (64 bins).
- **Coordinate Variance**: Variance of assigned coordinates per epoch (FR-009), computed as the sum of variances of x and y coordinates (trace of the covariance matrix).

### Statistical Analysis
- **Paired t-tests**: Comparing spatial vs. baseline scores across 5 seeds (FR-005).
  - *Hypotheses*: H0: mean difference = 0, H1: mean difference != 0.
- **Multiple Comparison Correction**: Bonferroni or Holm-Bonferroni (FR-006) applied across the 3 datasets (family of tests).
- **Effect Size**: Cohen's d with 95% CI (FR-007), using pooled standard deviation and non-central t-distribution for CI calculation.
- **Normality Check**: Shapiro-Wilk test; if p < 0.05, Wilcoxon signed-rank test is used.

*Note: With N=5, the statistical power to detect a medium effect size (Cohen's d=0.5) is approximately 0.18. The study is underpowered and results will be treated as exploratory. The analysis is designed to detect large effects only.*

## Compute Feasibility

### CPU-First Strategy
The implementation is designed for CPU execution on GitHub Actions free-tier (1 CPU core, 6 GB RAM).

The research question, method, and references are preserved as specified in the original planning document.
- **Model Loading**: 4-bit quantization ensures the model fits within RAM.
- **Batch Size Reduction**: Automatic reduction to 4 if peak RSS > 6.0 GB.
- **Dataset Streaming**: `datasets.load_dataset(..., streaming=True)` avoids loading entire datasets into memory.
- **Runtime Limit**: 5 hours total for 15 runs (3 datasets × 5 seeds) + analysis.

### GPU Escape Hatch
If the implementation requires CUDA (e.g., for 8-bit quantization or specific CUDA kernels), the execution stage will auto-offload to Kaggle's free GPU (~16 GB VRAM). The plan includes a scaled-down form:
- **Model**: 8-bit quantized `gpt2-medium`
- **Subset**: 100 examples per dataset
- **Steps**: 100 training steps
- **Device**: `cuda`

*Note: The primary plan is CPU-first. The GPU escape hatch is only triggered if the CPU run fails due to CUDA requirements.*

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| 4-bit Quantization | Essential for fitting 355M parameters in 6 GB RAM on CPU. |
| 8×8 Grid (64 slots) | Balances capacity with computational overhead. |
| Cosine Similarity | Standard for soft-addressed retrieval; aligns with FR-002. |
| Bonferroni Correction | Conservative method for controlling family-wise error across 3 datasets. |
| Streaming Data | Prevents OOM errors on large datasets. |
| [deferred] Subsample Cap | Resolves FR-010's placeholder with a concrete, implementable logic. |

## Limitations

- **Power**: 5 seeds may be insufficient for high statistical power; results are treated as exploratory.
- **Dataset Size**: Subsampling may reduce generalizability; results are reported as associational.
- **Causal Claims**: Findings are correlational; no randomization of architecture is performed.
- **Binding Problem**: Addressed via soft-addressed read; explicit binding architectures are deferred.
- **Dataset Proxies**: bAbI and LAMBADA are proxies for 'episodic' memory; the 'episodic' nature is simulated via task structure.
- **Training Window**: Short training (3 epochs) may limit convergence; results reflect the model's ability to adapt quickly.
- **Category Error**: The comparison is between different memory mechanisms (slots vs. attention), not just spatial vs. non-spatial organization of the same mechanism. This limits the isolation of the "spatial" benefit.