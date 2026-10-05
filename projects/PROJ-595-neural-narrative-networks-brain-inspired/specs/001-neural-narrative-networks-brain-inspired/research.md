# Research: Neural Narrative Networks

## Executive Summary

This research investigates whether incorporating hippocampal-like pattern separation (via Sparse Autoencoders) and prefrontal-like executive control (via Gating Modules) into narrative generation models yields hidden state representations that are more similar to human fMRI activation patterns during story comprehension than standard LSTM architectures. The study utilizes the OpenNeuro dataset for neural data and the ROCStories corpus for text.

**Critical Constraint**: The model will process *only* the specific story stimuli present in the fMRI dataset (the intersection). It will not generate new stories. If the intersection is insufficient (N < 10), the analysis is untestable and halts.

## Dataset Strategy

### Neural Data (fMRI)

- **Source**: OpenNeuro ds001495.
- **Verified URLs**:
 - `
 - `
- **Variables**: BOLD timecourses for Left Hippocampus, Right Hippocampus, and Dorsolateral Prefrontal Cortex (DLPFC).
- **Strategy**:
 1. Load the parquet dataset.
 2. Apply Harvard-Oxford masks (thresholded, linear registration to MNI) or coordinate-based fallback to extract ROI timecourses.
 3. **HRF-Aligned Extraction**: Use a Finite Impulse Response (FIR) model to deconvolve the BOLD signal, addressing the hemodynamic lag and temporal misalignment. Do not simply average.
 4. **Dataset Verification**: Check for the presence of event-locked annotations in the dataset metadata. If absent, halt with E002 (Data Availability Risk).
 5. **Intersection Check**: Identify the set of stories present in both the fMRI dataset and the ROCStories corpus. If N < 10, halt with E002.
- **Feasibility**: The dataset is available via Hugging Face `datasets` library. Streaming and chunked loading (subject-by-subject) will be used to avoid RAM overflow.

### Text Data (Stories)

- **Source**: ROCStories Corpus.
- **Verified URLs**:
 - `
 - `
- **Variables**: Story text, event boundaries (if present).
- **Strategy**:
 1. Download the training split.
 2. **Fallback**: If `event_boundaries` are missing, infer them using NLTK sentence segmentation and a heuristic for event transitions. If inference fails, halt with E001.
 3. **Intersection**: Filter to the set of stories that match the fMRI stimuli.
- **Feasibility**: Parquet/CSV formats are directly loadable.

### Model Data (Processed)

- **Source**: Internal processing of shared stories by SAE and TinyLSTM.
- **Strategy**: Process the exact story stimuli from the fMRI dataset. Store hidden states for RSA.

## Methodological Rigor

### Statistical Analysis: RSA & Permutation Testing

- **Method**: Representational Similarity Analysis (RSA) will compute the correlation between the model's hidden state RDM and the human fMRI RDM.
- **Primary Test**: A permutation test on the *difference* of correlations (Model A vs. Human minus Model B vs. Human). This directly tests the hypothesis that Model A is *better* than Model B.
- **Multiple Comparison Correction**: Bonferroni or Holm-Bonferroni correction will be applied to the final p-values for multiple ROIs.
- **Power Justification**: The permutation test will run with a sufficient number of permutations. Convergence is defined as p-value variance < 0.001 over the final 1,000 permutations (computed using `numpy.var(p_values[-1000:])`). If the dataset size limits power, this will be explicitly acknowledged as a limitation.
- **Causal Inference**: This is an observational study of model representations vs. neural data. Claims will be framed as "associational alignment" rather than causal proof of mechanism.
- **Collinearity**: If predictors (e.g., story length vs. complexity) are correlated, their effects will be reported descriptively, and independent effects will not be claimed without orthogonalization.

### Confounding Control

- **Capacity Matching**: The SAE and TinyLSTM models will be constrained to have similar parameter counts to ensure that any difference in RSA alignment is attributable to the architecture (pattern separation/gating) rather than capacity.
- **Shuffled Baseline**: A shuffled baseline (preserving statistics but destroying temporal structure) will be used to verify that the RSA signal is not spurious.

### Dataset Variable Fit

- **Check**: The OpenNeuro ds001495 dataset must contain BOLD timecourses for the specified ROIs and event-locked annotations.
- **Mismatch Handling**: If the dataset lacks DLPFC masks, the plan falls back to coordinate-based extraction. If the dataset lacks story-condition labels entirely, the RSA cannot be computed per event, and the plan will pivot to whole-story RSA (noting the reduced temporal resolution).
- **Fatal Flaw**: If the dataset lacks *both* masks and coordinates for the required ROIs, or lacks event-locked annotations for the shared stories, the study is halted as untestable (E002).

## Compute Feasibility & Time Complexity

### CPU-First Strategy

- **Model Architecture**:
 - **SAE**: Implemented in PyTorch with `torch.no_grad()` where possible. Hidden dimensionality will be constrained to fit within ~ GB RAM for the layer.
 - **Baseline**: TinyLSTM (quantized) to ensure memory efficiency.
- **Data Streaming**: The `datasets` library will be used with `streaming=True` to load fMRI data in chunks, preventing RAM overflow. fMRI data will be loaded subject-by-subject using `nibabel` with memory mapping.
- **Training/Processing**: The SAE will process the shared stories (N < 100) to ensure completion within the 6-hour job limit.

### Time Complexity Estimate

- **RSA**: Computation of correlation matrices for 20 subjects x 10 events x 512 dimensions is ~10MB of data.
- **Permutation Test**: iterations is the bottleneck. The test will be parallelized across the available CPU cores. If the full run exceeds 4 hours, a subset of permutations will be used, with a note on power limitation.

### GPU Escape Hatch

- **Trigger**: If the SAE processing or RSA computation fails due to memory constraints on the CPU runner, the execution pipeline will detect the CUDA requirement (if any) and re-run on a Kaggle GPU.
- **Scaled GPU Form**: If a GPU is required, the plan will use an 8-bit quantized model (`load_in_8bit=True`) and a reduced dataset subset to fit within ~16 GB VRAM.
- **No Fabrication**: No synthetic CPU approximations of GPU-only methods will be used.

## Decision/Rationale

- **Why SAE for Pattern Separation?** The Sparse Autoencoder enforces a sparsity constraint (activation density ≤ 0.20), mimicking the sparse coding observed in the Dentate Gyrus.
- **Why RSA?** RSA allows direct comparison of high-dimensional representational structures between models and brains without requiring pixel-wise or timepoint-wise alignment.
- **Why CPU?** The GitHub Actions free tier is the target deployment environment. The methods are selected to be tractable on this hardware.
- **Why HRF-Aligned Extraction?** Simple averaging introduces noise due to hemodynamic lag. FIR modeling provides a more accurate temporal alignment.
