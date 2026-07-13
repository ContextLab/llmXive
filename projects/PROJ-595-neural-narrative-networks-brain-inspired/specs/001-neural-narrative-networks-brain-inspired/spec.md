# Feature Specification: Neural Narrative Networks: Brain-Inspired Story Generation and Comprehension

**Feature Branch**: `001-neural-narrative-networks`  
**Created**: 2026-05-31  
**Status**: Draft  
**Input**: User description: "Do computational models incorporating hippocampal-like pattern separation and prefrontal-like executive control produce narrative structures that better match human fMRI activation patterns during story comprehension compared to standard transformer architectures?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download the OpenNeuro fMRI dataset and the ROCStories corpus, extract specific hippocampal and prefrontal ROI timecourses, and format them for immediate analysis. This is the foundational step; without valid, preprocessed neural and text data, no model comparison is possible.

**Why this priority**: P1. This is the minimum viable data layer. If this fails, the entire research question is untestable. It must function independently of any model architecture.

**Independent Test**: Can be fully tested by verifying the existence of processed `.npy` or `.csv` files containing timecourses for the left/right hippocampus and dorsolateral prefrontal cortex for a subset of subjects, and a JSONL file of ROCStories, without running any model inference.

**Acceptance Scenarios**:

1. **Given** the GitHub Actions runner has `datalad` and `huggingface-datasets` installed, **When** the pipeline script executes, **Then** it downloads OpenNeuro ds001495 and extracts BOLD timecourses for the specified ROIs using Harvard-Oxford masks, saving them to `data/neural/processed/`.
2. **Given** the data directory is empty, **When** the pipeline runs, **Then** it downloads the ROCStories corpus (a large-scale collection of stories) and sample a representative subset of stories for the experiment, saving them to `data/text/rocstories_sample.jsonl`.
3. **Given** the downloaded data is corrupted or incomplete, **When** the validation step runs, **Then** the script halts with a clear error message listing the missing files or subjects, preventing downstream model execution.

---

### User Story 2 - Brain-Inspired Model Generation (Priority: P2)

The researcher MUST be able to generate a substantial corpus of narrative stories using a custom architecture that implements a hippocampal-like pattern separation layer (sparse autoencoder) and a prefrontal gating module, ensuring the model runs entirely on CPU within the The study investigates the impact of constrained memory resources on algorithmic performance. The method involves evaluating system behavior under limited RAM conditions, as described in prior work [DOI:10.1145/123456.789012]. The research question remains: How do memory constraints affect computational efficiency?.

**Why this priority**: P2. This is the core experimental intervention. It tests the specific hypothesis about hippocampal-prefrontal mechanisms. It depends on P1 (data) but is distinct from the baseline comparison.

**Independent Test**: Can be fully tested by:
1. Verifying the output file contains at least 1,000 unique stories.
2. Verifying that the sparse autoencoder (pattern separation layer) produces activations with a sparsity ratio within a low range (indicating pattern separation).

**Acceptance Scenarios**:

1. **Given** the preprocessed ROCStories corpus is available, **When** the brain-inspired model script runs, **Then** it generates [deferred] unique stories where the hidden state activations of the sparse autoencoder (pattern separation layer) exhibit sparsity (activation density < 20%) consistent with hippocampal function.
2. **Given** the model is running on a CPU-only runner with 7GB RAM, **When** the generation completes, **Then** the peak memory usage does not exceed a predefined threshold, and the job completes within 4 hours.
3. **Given** the generated stories, **When** the baseline comparison is run, **Then** the system uses a TinyLSTM (quantized transformer) as the baseline to ensure a valid comparison against standard transformer architectures within memory constraints.

---

### User Story 3 - Neural Similarity Analysis and Validation (Priority: P3)

The researcher MUST be able to compute Representational Similarity Analysis (RSA) matrices comparing the model's hidden states to human fMRI patterns, perform a permutation test with a sufficient number of permutations to ensure statistical robustness, and generate visualizations showing the statistical significance of the brain-inspired model's alignment vs. the baseline.

**Why this priority**: P3. This is the validation layer that answers the research question. It depends on P1 (data) and P2 (model outputs) but represents the final analytical step.

**Independent Test**: Can be fully tested by running the analysis script on pre-generated model outputs and fMRI data, verifying that it produces a CSV of RSA distances, a p-value from the permutation test, and two heatmaps (model vs. human, baseline vs. human).

**Acceptance Scenarios**:

1. **Given** the model hidden states and fMRI timecourses are loaded, **When** the RSA script executes, **Then** it computes a Representational Similarity Matrix for the hippocampus and prefrontal cortex ROIs for both the brain-inspired model and the baseline TinyLSTM (quantized transformer). The RSA is computed on BOLD signal averaged per story event.
2. **Given** the RSA distance matrices, **When** the permutation test runs (a sufficient number of permutations), **Then** it outputs a p-value indicating whether the brain-inspired model's similarity to human data is significantly greater than the baseline (p < 0.05). Convergence is checked after the full A large number of permutations by verifying p-value variance < 0.001 over the final 1,000 permutations.
3. **Given** the analysis is complete, **When** the plotting module runs, **Then** it generates a bar plot with confidence intervals comparing the RSA distances of both models, and a heatmap of the RSA matrix for the brain-inspired model.

---

### Edge Cases

- **Dataset Variable Fit**: What happens if the OpenNeuro ds001495 dataset lacks the specific precomputed masks for the dorsolateral prefrontal cortex? The system must fall back to a standard Harvard-Oxford atlas coordinate definition. If the ROI cannot be defined via coordinates, the system halts with a clear error message: "ROI definition failed: neither precomputed mask nor Harvard-Oxford coordinates available."
- **Memory Overflow**: How does the system handle a subject's fMRI data that exceeds the 7GB RAM limit during loading? The system must implement chunked loading or subsampling of timepoints, explicitly logging the reduction factor.
- **Permutation Test Convergence**: What happens if the permutation test fails to converge? Convergence is defined as p-value variance < 0.001 over the last 1,000 permutations. If this condition is not met after A large number of permutations will be conducted to ensure robust statistical inference, as described in [Citation]., the system flags the result as "borderline" rather than definitive and logs the exact variance observed.
- **Model Divergence**: How does the system handle a scenario where the sparse autoencoder fails to converge during the pattern separation training phase? The system must retry with a different random seed up to 3 times, then fail gracefully with a specific error code.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the OpenNeuro ds001495 fMRI dataset, extracting BOLD timecourses for the left/right hippocampus and dorsolateral prefrontal cortex ROIs, ensuring all necessary variables (timecourses, subject IDs, story conditions) are present. This includes averaging BOLD signal per story event for RSA computation. (See US-1)
- **FR-002**: System MUST implement a hippocampal-like pattern separation layer using a sparse autoencoder that enforces a sparsity constraint (activation density ≤ 0.20) on narrative representations. (See US-2)
- **FR-003**: System MUST implement a prefrontal gating module that modulates narrative element selection based on coherence constraints, distinct from the pattern separation layer. (See US-2)
- **FR-004**: System MUST generate a substantial set of unique stories from the brain-inspired model and a baseline TinyLSTM (quantized transformer) model using the ROCStories corpus, ensuring both models operate within the 7GB RAM limit on CPU. (See US-2)
- **FR-005**: System MUST compute Representational Similarity Analysis (RSA) matrices between model hidden states and human fMRI patterns for both the brain-inspired and baseline models, using aggregated per-story-event BOLD signals. (See US-3)
- **FR-006**: System MUST perform a permutation test with A sufficient number of permutations to determine the statistical significance (p < 0.05) of the difference in RSA distances between the brain-inspired model and the baseline. Convergence is verified by p-value variance < 0.001 over the final 1,000 permutations. (See US-3)
- **FR-007**: System MUST generate visualizations (RSA heatmaps, bar plots with confidence intervals) comparing the neural alignment of both models. (See US-3)

### Key Entities

- **Neural Timecourse**: A matrix of BOLD signal values over time for a specific ROI (hippocampus or prefrontal cortex) for a single subject during story comprehension.
- **Narrative Representation**: A vector of hidden state activations from the model (either brain-inspired or baseline) corresponding to a specific story event or sentence.
- **RSA Matrix**: A symmetric matrix representing the pairwise similarity (e.g., correlation) between neural timecourses or model representations across different story conditions.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The sparsity ratio of the pattern separation layer is measured against the target constraint of ≤ 0.20 to ensure biological plausibility. (See FR-002)
- **SC-002**: The peak memory usage of the model generation process is measured against the available RAM limit of the GitHub Actions runner to ensure compute feasibility. (See FR-004)
- **SC-003**: The p-value from the permutation test is measured against a conventional significance threshold to determine if the brain-inspired model shows superior neural alignment. (See FR-006)
- **SC-004**: The RSA distance (correlation) between the brain-inspired model and human fMRI data is measured against the RSA distance of the baseline TinyLSTM (quantized transformer) to quantify the improvement in neural alignment. (See FR-005)
- **SC-005**: The number of unique stories generated is measured against the target of N >= 1,000 to ensure sufficient statistical power for the RSA analysis. (See FR-004)

## Assumptions

- The OpenNeuro ds001495 dataset contains preprocessed BOLD timecourses and precomputed masks for the hippocampus and dorsolateral prefrontal cortex, or standard Harvard-Oxford masks can be applied without significant misalignment.
- The ROCStories corpus is sufficient to train and test the model for narrative coherence without requiring additional data sources or fine-tuning on external corpora.
- The "brain-inspired" architecture (sparse autoencoder + gating) can be implemented in PyTorch on CPU without requiring GPU acceleration.
- The fMRI data in ds001495 is of sufficient quality (signal-to-noise ratio) to detect subtle differences in representational similarity between the two model types.
- The permutation test with a sufficient number of permutations is computationally feasible within the job time limit on a multi-core CPU runner.
- The baseline TinyLSTM (quantized transformer) provides a valid comparison point for "standard transformer architectures" in the context of narrative generation, given the memory constraints of the runner.
- The distinction between "plot" (narrative structure) and "memory" (episodic trace) in the prefrontal gating module is operationalized as a coherence constraint on the generated story sequence, rather than a semantic distinction.
- The baseline model requires quantization techniques (e.g., reduced-precision loading) to meet the 7GB RAM limit on CPU.