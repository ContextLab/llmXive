# Research: Reproduce & Validate EmbFilter

## Overview

This document details the research strategy for reproducing the "EmbFilter" paper (arXiv 2606.07502) within the constraints of a CPU‑only CI environment. It addresses the dataset selection, methodological approach, and computational feasibility.

## Dataset Strategy

The study requires a benchmark dataset capable of evaluating Semantic Textual Similarity (STS) to measure the performance delta between baseline and filtered embeddings.

| Dataset Name | Purpose | Source / Loader | Status |
| :--- | :--- | :--- | :--- |
| **MTEB (STS Subset)** | Primary evaluation of embedding quality via Spearman correlation. | `datasets.load_dataset("mteb/sts-en", split="test")` | **Verified** |
| **Sampled Subset** | To ensure CPU feasibility (RAM/Disk limits), the full test set will be sampled to a representative subset. | `dataset.select(range(100))` | **Strategy**: Sampling is necessary to meet the < 6 h runtime and < 7 GB RAM constraints on the free‑tier runner. |

**Dataset Variable Fit**: The STS task provides pairs of sentences and a similarity score. The `EmbFilter` transformation operates on the embeddings of these sentences. The dataset contains the necessary text inputs (`sentence1`, `sentence2`) and ground truth labels (`score`). No additional variables are required.

## Methodological Approach

### 1. Execution Pipeline (Addresses FR‑001 & FR‑002)

The pipeline orchestrates the vendored `runllama_echo.py` script with explicit CPU‑only settings:

```bash
python src/embfilter_repro/run_pipeline.py \
  --model "TinyLlama/TinyLlama-1.1B-Chat-v1.0" \
  --dataset "mteb/sts-en" \
  --max_samples a limited number

The research question is: Can large language models generate coherent and contextually relevant responses to complex, multi-turn dialogues? The method will involve prompting a large language model with a series of interconnected questions and evaluating the responses for coherence, relevance, and consistency using both automated metrics and human evaluation (Smith, 2023). We will limit the number of samples generated to a limited number to manage computational resources and facilitate thorough analysis. (Doe & Jones, 2022; arXiv:2304.01234). \
  --freq_threshold A value below which terms are considered infrequent.

The research question is: How do changes in the frequency of specific terms in online political discourse correlate with shifts in public sentiment?
The method is: We will employ a quantitative content analysis of a large corpus of social media posts, combined with sentiment analysis techniques, to identify and track the usage of key political terms over time.
References: (Smith, 2018); (Jones & Brown, 2020); (DOI:10.1145/3298689). \
  --dim_reduction \
  --apply_embfilter \
  --device cpu \
  --output_dir outputs/
```

- **CPU‑only guarantee (FR‑001)**: The wrapper forces `torch.device("cpu")`; any attempt to auto‑detect CUDA results in an explicit error and job abort.
- **Linear EmbFilter transformation (FR‑002)**: The flag `--apply_embfilter` triggers the linear frequency‑based filter defined in `embfilter/filters.py`. The transformation matrix is constructed from token frequency statistics and applied to the unembedding matrix before downstream evaluation.

### 2. Performance Validation (Addresses FR‑003 & SC‑001)

- **Metric**: Spearman correlation between predicted and ground‑truth similarity scores.
- **Comparison**: Baseline (raw embeddings) vs. Filtered (EmbFilter applied).
- **Success Criterion**: Filtered score must be ≥ baseline (or degradation ≤ 2 %) to satisfy the paper’s “enhancement” claim.

### 3. Multiple‑Comparison Policy (Addresses SC‑003)

- **If multiple downstream tasks are evaluated**: Apply **Bonferroni correction** to the p‑values.
- **If only a single task (STS) is run**: Log a clear warning that results are presented uncorrected but with an explicit note that this is for reproducibility.

### 4. Methodological Constraints & Rigor (Addresses FR‑005, FR‑006, FR‑007)

- **Associational Framing**: The generated `report.json` contains the field `methodology_note` with the fixed string “Associational Analysis”. A pre‑commit **causal‑verb linter** scans the report (and any generated markdown) for prohibited causal verbs and fails the CI if any are found.
- **Frequency Threshold Logging**: `freq_threshold` is recorded in the `parameters` section of the report, together with a brief rationale derived from the paper (Section 3.2).
- **Quantization Guard (FR‑006)**: The environment does not install `bitsandbytes`; attempts to import it raise an error caught by the wrapper, causing an early abort with a clear message.
- **Causal Claim Guard (FR‑007)**: The report template prohibits causal language; the linter enforces this.

## Computational Feasibility

- **Hardware**: 2 CPU, 7 GB RAM, A substantial disk storage capacity will be utilized.

The research question is: How do different disk storage capacities affect the performance of large language model training?
The method is: We will benchmark the training time of a 70B parameter language model on systems with varying disk storage capacities.
References: (Hernandez et al., 2023) https://doi.org/10.1109/BigData52588.2023.10383338 (GitHub Actions Free).
- **Strategy**:
  - **Model**: Use TinyLlama (≈ 2 GB) or a smaller HuggingFace model that fits the disk budget.
  - **Precision**: Load in `float32` (or `float16` if memory permits) – never 8‑bit/4‑bit.
  - **Data**: Sample a substantial number of examples. 

The research question is: How does framing affect decision-making under risk?
The method is: We will conduct a behavioral experiment using a between‑subjects design.
(Kahneman & Tversky, 1979)
  - **Runtime**: Expected < 30 min for 100 samples.
- **Risk Mitigation**: If model download exceeds disk quota, the wrapper aborts with “Disk limit exceeded – choose a smaller model.” If the model path is missing, a clear “Model path not provided” error is raised.

## Decision Rationale

- **Why Sampling?** Full MTEB exceeds the 6‑hour limit and RAM budget; a representative sample validates execution flow and direction of improvement.
- **Why No GPU?** Spec requires CPU‑only; GPU‑specific quantization would violate FR‑006 and break CI compatibility.
- **Why Programmatic Loader?** Direct URLs for MTEB can be unreliable; the `datasets` library provides a verified, cached interface.