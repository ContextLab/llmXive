# Feature Specification: Neural Narrative Networks: Brain-Inspired Story Generation and Comprehension

**Feature Branch**: `001-neural-narrative-networks`  
**Created**: 2026-05-31  
**Status**: Draft  
**Input**: User description: "Do computational models incorporating hippocampal-like pattern separation and prefrontal-like executive control produce narrative structures that better match human fMRI activation patterns during story comprehension compared to standard transformer architectures?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (US-1)

The researcher MUST be able to download the OpenNeuro fMRI dataset and the ROCStories corpus, extract specific hippocampal and prefrontal ROI timecourses, and format them for immediate analysis. This is the foundational step; without valid, preprocessed neural and text data, no model comparison is possible.

**Why this priority**: P1. This is the minimum viable data layer. If this fails, the entire research question is untestable. It must function independently of any model architecture.

**Independent Test**: Can be fully tested by verifying the existence of processed `.npy` or `.csv` files containing timecourses for the left/right hippocampus and dorsolateral prefrontal cortex for a subset of subjects, and a JSONL file of ROCStories, without running any model inference.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions runner has `datalad` and `huggingface-datasets` installed, **When** the pipeline script executes, **Then** it downloads OpenNeuro ds001495 and extracts BOLD timecourses for the specified ROIs using Harvard-Oxford masks, saving them to `data/neural/processed/`.
2. **Given** the data directory is empty, **When** the pipeline runs, **Then** it downloads the ROCStories corpus (a large-scale collection of stories) and samples a representative subset of stories for the experiment, saving them to `data/text/rocstories_sample.jsonl`.
3. **Given** the downloaded data is corrupted or incomplete, **When** the validation step runs, **Then** the script halts with a clear error message listing the missing files or subjects, preventing downstream model execution.

---

### User Story 2 - Brain-Inspired Model Generation (US-2)

The researcher MUST be able to generate a substantial corpus of narrative stories using a custom architecture that implements a hippocampal‑like pattern separation layer (sparse autoencoder) and a prefrontal gating module, ensuring the model runs entirely on CPU under a strict memory budget (≤ 2 GB). This directly tests the hypothesis that hippocampal‑prefrontal mechanisms improve neural alignment compared to a standard transformer baseline.

**Why this priority**: P2. This is the core experimental intervention. It tests the specific hypothesis about hippocampal‑prefrontal mechanisms. It depends on US‑1 but is distinct from the baseline comparison.

**Independent Test**: Can be fully tested by:
1. Verifying the output file contains at least 1,000 unique stories.
2. Verifying that the sparse autoencoder (pattern separation layer) produces activations with a sparsity ratio ≤ 0.20 and that the prefrontal gating module yields a StoryCoherence score ≥ 0.70 (see SC‑007).

**Acceptance Scenarios**:

1. **Given** the preprocessed ROCStories corpus is available, **When** the brain‑inspired model script runs, **Then** it generates ≥ 1,000 unique stories where the hidden‑state activations of the sparse autoencoder exhibit sparsity ≤ 20 % and the gating module achieves a coherence score ≥ 0.70.
2. **Given** the model is running on a CPU‑only runner with ≤ 2 GB RAM, **When** the generation completes, **Then** the peak memory usage does not exceed 2 GB and the job finishes within 4 hours.
3. **Given** the generated stories, **When** the baseline comparison is run, **Then** the system uses a quantized TinyBERT transformer (~4.4 M parameters) as the baseline to ensure a valid comparison against standard transformer architectures within the same memory constraints.

---

### User Story 3 - Neural Similarity Analysis and Validation (US-3)

The researcher MUST be able to compute Representational Similarity Analysis (RSA) matrices comparing the model's hidden states to human fMRI patterns, perform a permutation test with a fixed sufficiently large number of permutations, and generate visualizations showing the statistical significance of the brain‑inspired model's alignment vs. the baseline.

**Why this priority**: P3. This is the validation layer that answers the research question. It depends on US‑1 and US‑2 but represents the final analytical step.

**Independent Test**: Can be fully tested by running the analysis script on pre‑generated model outputs and fMRI data, verifying that it produces a CSV of RSA distances, a p‑value from the permutation test, and two visualizations (heatmaps and bar plot).

**Acceptance Scenarios**:

1. **Given** the model hidden states and fMRI timecourses are loaded, **When** the RSA script executes, **Then** it computes a Representational Similarity Matrix for the hippocampus and dorsolateral prefrontal cortex ROIs for both the brain‑inspired model and the baseline TinyBERT. RSA similarity is quantified using Spearman rank correlation (primary) with Pearson as a secondary check.
2. **Given** the RSA distance matrices, **When** the permutation test runs with a sufficiently large number of permutations, **Then** it outputs a p‑value indicating whether the brain‑inspired model's similarity to human data is significantly greater than the baseline (p < 0.05). No early‑stopping is used; the full permutation set ensures an unbiased null distribution.
3. **Given** the analysis is complete, **When** the plotting module runs, **Then** it generates a bar plot with confidence intervals comparing the RSA distances of both models, and a heatmap of the RSA matrix for the brain‑inspired model.

---

### Edge Cases

- **Dataset Variable Fit**: What happens if the OpenNeuro ds001495 dataset lacks the specific precomputed masks for the dorsolateral prefrontal cortex? The system must fall back to a standard Harvard‑Oxford atlas coordinate definition. If the ROI cannot be defined via coordinates, the system halts with a clear error message: "ROI definition failed: neither precomputed mask nor Harvard‑Oxford coordinates available."
- **Memory Overflow**: How does the system handle a subject's fMRI data that exceeds the GB RAM limit during loading? The system must implement chunked loading or subsampling of timepoints, explicitly logging the reduction factor.
- **Permutation Test Convergence**: What happens if the permutation test fails to converge? Convergence is defined as p‑value variance < 0.001 over the last 1,000 permutations. If this condition is not met after the full A substantial number of permutations., the system flags the result as "borderline" and logs the observed variance.
- **Model Divergence**: How does the system handle a scenario where the sparse autoencoder fails to converge during the pattern separation training phase? The system must retry with a different random seed up to 3 times, then fail gracefully with a specific error code.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the OpenNeuro ds001495 fMRI dataset, extracting BOLD timecourses for the left/right hippocampus and dorsolateral prefrontal cortex ROIs, ensuring all necessary variables (timecourses, subject IDs, story conditions) are present. This includes averaging BOLD signal per story event for RSA computation. (See US-1)
- **FR-002**: System MUST implement a hippocampal‑like pattern separation layer using a sparse autoencoder that enforces a sparsity constraint (activation density ≤ 0.20) on narrative representations. (See US-2)
- **FR-003**: System MUST implement a prefrontal gating module that modulates narrative element selection based on a coherence metric, achieving a StoryCoherence score ≥ 0.70. (See US-2)
- **FR-004**: System MUST generate a substantial set of unique stories from the brain‑inspired model and a baseline quantized TinyBERT transformer (≈ a few M parameters) model using the ROCStories corpus, ensuring both models operate within the ≤ 2 GB RAM limit on CPU. (See US-2)
- **FR-005**: System MUST compute Representational Similarity Analysis (RSA) matrices between model hidden states and human fMRI patterns for both the brain‑inspired and baseline models, using Spearman rank correlation as the primary similarity metric. (See US-3)
- **FR-006**: System MUST perform a permutation test with **10,000** permutations to determine the statistical significance (p < 0.05) of the difference in RSA distances between the brain‑inspired model and the baseline. (See US-3)
- **FR-007**: System MUST generate visualizations (RSA heatmaps, bar plots with confidence intervals) comparing the neural alignment of both models. (See US-3)
- **FR-008**: System MUST conduct a Monte‑Carlo power analysis for the RSA comparison across the two ROIs (hippocampus, dorsolateral prefrontal cortex), targeting ≥ 80 % statistical power to detect a medium effect size (Cohen's d = 0.5). The analysis must be documented and its estimated power reported. (See US-3)
- **FR-009**: System MUST compute RSA per subject, then aggregate results using a linear mixed‑effects model to account for inter‑subject variability, reporting mixed‑effects p‑values. (See US-3)
- **FR-010**: System MUST save the pre‑training representation of the sparse autoencoder (a `.pt` file of hidden‑state vectors) and validate its integrity before downstream use. (See US-2)
- **FR-011**: System MUST ensure that any model used (brain‑inspired or baseline) contains ≤ 5 M trainable parameters, satisfying the CPU‑only memory budget. (See US-2)

### Key Entities

- **Neural Timecourse**: A matrix of BOLD signal values over time for a specific ROI (hippocampus or prefrontal cortex) for a single subject during story comprehension.
- **Narrative Representation**: A vector of hidden state activations from the model (either brain‑inspired or baseline) corresponding to a specific story event or sentence.
- **RSA Matrix**: A symmetric matrix representing the pairwise similarity (e.g., Spearman correlation) between neural timecourses or model representations across different story conditions.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The sparsity ratio of the pattern separation layer is measured against the target constraint of ≤ 0.20 to ensure biological plausibility. (See FR-002)
- **SC-002**: The peak memory usage of the model generation process is measured against the available RAM limit of **2 GB** on the GitHub Actions runner to ensure compute feasibility. (See FR-004)
- **SC-003**: The p‑value from the permutation test is measured against a conventional significance threshold (p < 0.05) to determine if the brain‑inspired model shows superior neural alignment. (See FR-006)
- **SC-004**: The RSA distance (Spearman correlation) between the brain‑inspired model and human fMRI data is measured against the RSA distance of the baseline TinyBERT transformer to quantify the improvement in neural alignment. (See FR-005)
- **SC-005**: The number of unique stories generated is measured against the target of **N ≥ 1,000** to ensure sufficient statistical power for the RSA analysis. (See FR-004)
- **SC-006**: All required processed files (neural timecourses, subject metadata, ROCStories sample) exist and pass validation checks. (See US-1)
- **SC-007**: The prefrontal gating module achieves a StoryCoherence score ≥ 0.70 on the held‑out validation set. (See FR-003)
- **SC-008**: The power analysis reports an estimated power ≥ 80 % for detecting a medium effect size (d = 0.5) across the two ROIs. (See FR-008)
- **SC-009**: Mixed‑effects RSA analysis reports p‑values that account for inter‑subject variability, with model fit diagnostics meeting standard thresholds (e.g., AIC reduction). (See FR-009)
- **SC-010**: The pre‑training SAE representation file (`pretrained_sae.pt`) is present, loads without error, and its activation statistics match the sparsity constraint (≤ 0.20). (See FR-010)

## Assumptions

- The OpenNeuro dataset contains preprocessed BOLD timecourses and precomputed masks for the hippocampus and dorsolateral prefrontal cortex, or standard Harvard‑Oxford masks can be applied without significant misalignment.
- The ROCStories corpus is sufficient to train and test the model for narrative coherence without requiring additional data sources or fine‑tuning on external corpora.
- The "brain‑inspired" architecture (sparse autoencoder + gating) can be implemented in PyTorch on CPU without requiring GPU acceleration.
- The fMRI data from a suitable open‑access dataset is of sufficient quality (signal‑to‑noise ratio) to detect subtle differences in representational similarity between the two model types.
- The permutation test with 10,000 permutations is computationally feasible within the job time limit on a multi‑core CPU runner.
- The baseline quantized TinyBERT transformer (~4.4 M parameters) satisfies the ≤ 5 M parameter constraint and the CPU‑only memory budget.
- The distinction between "plot" (narrative structure) and "memory" (episodic trace) in the prefrontal gating module is operationalized as a coherence constraint on the generated story sequence.
- The baseline model uses quantization techniques (e.g., 8‑bit integer) to meet the constrained RAM limit on CPU.
