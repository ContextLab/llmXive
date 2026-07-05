# Feature Specification: Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Feature Branch**: `001-narrative-archaeology`  
**Created**: 2026-05-26  
**Status**: Draft  
**Input**: User description: "How do neural activity patterns during story recall differ from those during initial encoding, and to what extent can these patterns be decoded to reconstruct specific narrative elements (plot points, characters, themes) using publicly available fMRI datasets?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download the Natural Stories fMRI dataset (OpenNeuro ds000234), preprocess it using fMRIPrep, and segment the story into discrete events with associated metadata (plot points, characters, themes) to create a clean, analysis-ready dataset.

**Why this priority**: Without a reproducible, clean dataset aligned with event annotations, no decoding or comparison analysis can proceed. This is the foundational block for all subsequent research steps.

**Independent Test**: Can be fully tested by running the pipeline on a subset of 2 subjects and verifying that the output contains preprocessed NIfTI files, a JSON event table with timestamps, and that the event count matches the story annotation file.

**Acceptance Scenarios**:

1. **Given** a valid OpenNeuro dataset ID, **When** the pipeline executes on a GitHub Actions ubuntu-latest runner (vCPU, 7GB RAM) with parallel workers, **Then** it downloads the raw data and runs fMRIPrep, completing preprocessing for a 10-subject subset within 6 hours.
2. **Given** the preprocessed fMRI data, **When** the event segmentation module runs, **Then** it outputs a CSV file mapping timepoints to specific narrative elements (plot, character, theme) with ≤ 5% missing timepoints.
3. **Given** the segmented data, **When** the researcher inspects the ROI masks, **Then** the masks for hippocampus, mPFC, PCC, and lateral temporal cortex are correctly aligned to the preprocessed space.

---

### User Story 2 - Encoding vs. Recognition Pattern Comparison (Priority: P2)

The researcher needs to compare neural activity patterns between the encoding (listening) and recognition (delayed task) phases to identify regions where patterns overlap and where they diverge, specifically focusing on hippocampal and prefrontal reconfiguration.

**Why this priority**: This addresses the core research question regarding the transformation of memory traces. It establishes the baseline for whether reconstruction is even theoretically possible.

**Independent Test**: Can be fully tested by computing Representational Similarity Analysis (RSA) matrices for encoding and recognition phases and verifying that the dissimilarity between encoding-recognition pairs is significantly higher than encoding-encoding pairs (dissimilarity difference > 0.1 or p < 0.05).

**Acceptance Scenarios**:

1. **Given** preprocessed timecourses for encoding and recognition, **When** the RSA module computes dissimilarity matrices, **Then** it outputs a dissimilarity matrix showing distinct reconfiguration in the hippocampus compared to sensory cortices (dissimilarity difference > 0.1 or p < 0.05).
2. **Given** the dissimilarity matrices, **When** the system performs a permutation test (A sufficient number of iterations will be performed to ensure convergence of the algorithm, as outlined in the research question and method, following the framework established by the cited references.) with FDR correction (q < 0.05) across ROIs, **Then** it reports a p-value indicating whether the observed pattern dissimilarity difference is statistically significant.
3. **Given** the results, **When** the researcher visualizes the top differing ROIs, **Then** the mPFC and hippocampus are highlighted as having the largest divergence scores.

---

### User Story 3 - Narrative Element Reconstruction (Priority: P3)

The researcher needs to train linear classifiers to predict specific narrative elements (plot points, characters, themes) from neural patterns during recognition and evaluate if plot points are reconstructed with higher accuracy than character details.

**Why this priority**: This is the ultimate "archaeology" step—attempting to reverse-engineer the story content. It validates the practical utility of the memory traces identified in US-2.

**Independent Test**: Can be fully tested by training a ridge regression classifier on A substantial majority of the recognition data (with semantic feature extraction) and evaluating accuracy on the held-out A balanced distribution across each narrative category, verifying accuracy exceeds the calculated chance level (1/N) for at least one category.

**Acceptance Scenarios**:

1. **Given** the labeled recognition fMRI data, **When** the decoder trains a linear model with K-fold cross-validation using semantic features (N=20 for plot points), **Then** it reports the observed decoding accuracy for each category.
2. **Given** the trained model, **When** it attempts to reconstruct character details (N=10), **Then** the accuracy is recorded and compared to plot point accuracy to test for statistical difference.
3. **Given** the reconstruction results, **When** a null model (shuffled labels) is tested, **Then** the real model's performance is significantly higher (p < 0.01) than the null distribution.

### Edge Cases

- What happens if the fMRIPrep preprocessing fails for a specific subject due to motion artifacts? The system must skip the subject and log the error, proceeding with the remaining subjects rather than halting the entire pipeline.
- How does the system handle the temporal misalignment between the fMRI BOLD signal (slow) and the rapid onset of narrative events? The system must apply a hemodynamic response function (HRF) convolution to align event labels with neural data before training.
- What if the dataset lacks sufficient samples for a specific narrative category (e.g., rare themes)? The system must aggregate rare categories into a "miscellaneous" bin or exclude them from the specific classifier to prevent overfitting.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess fMRI data from OpenNeuro ds000234 using fMRIPrep on a GitHub Actions ubuntu-latest runner with -core parallelization, completing a 10-subject subset within 6 hours (See US-1).
- **FR-002**: System MUST segment the continuous story timeline into discrete events (plot, character, theme) and align these labels with the preprocessed BOLD signal timecourses (See US-1).
- **FR-003**: System MUST extract timecourse data from specific Regions of Interest (hippocampus, mPFC, PCC, lateral temporal cortex) for both encoding and recognition phases (See US-2).
- **FR-004**: System MUST compute Representational Similarity Analysis (RSA) dissimilarity matrices to quantify the difference between encoding and recognition neural patterns and perform permutation testing for significance (See US-2).
- **FR-005**: System MUST train linear classifiers (ridge regression or SVM) to predict narrative elements from recognition patterns using semantic feature extraction and report cross-validated accuracy against a chance baseline (1/N) (See US-3).
- **FR-006**: System MUST implement a multiple-comparison correction (e.g., FDR q < 0.05) when testing significance across multiple narrative categories and ROIs to control family-wise error (See US-3).
- **FR-007**: System MUST extract semantic features using a pre-trained model (e.g., BERT or CLIP) to map fMRI data to semantic space before classification (See US-3).

### Key Entities

- **NeuralPattern**: A vector representing the BOLD signal amplitude across voxels in a specific ROI at a specific timepoint, associated with an event label.
- **NarrativeEvent**: A discrete unit of the story defined by its type (plot, character, theme), timestamp, and semantic content.
- **DecodingModel**: A trained linear classifier mapping SemanticFeature inputs to NarrativeEvent labels, storing weights and performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Decoding accuracy for narrative elements is measured against a null distribution generated by a sufficient number of permutations of event labels to establish statistical significance (See US-3).
- **SC-002**: Pattern dissimilarity between encoding and recognition is measured against the dissimilarity within the same phase (encoding-encoding) to quantify memory reconfiguration (See US-2).
- **SC-003**: The false-positive rate of the decoding model is measured against the expected chance level (1/N for N-class, where N=20 for plot points, N=10 for characters) corrected for multiple comparisons (See US-3).
- **SC-005**: Computational feasibility is measured against the constraint of completing the full analysis (preprocessing + decoding) for a 10-subject subset on a GitHub Actions free-tier runner (parallel workers) within 6 hours (See FR-001).

## Constraints

- **C-001**: The full analysis must complete within 6 hours on a GitHub Actions free-tier runner (2 vCPU, 7GB RAM) with parallel workers, processing a subject subset.

## Assumptions

- The OpenNeuro ds000234 dataset contains sufficient temporal resolution and signal-to-noise ratio to detect event-related patterns in the hippocampus and mPFC without requiring ultra-high-field scanners.
- The provided story annotation files (event onset/duration) are accurate and sufficient to align with the fMRI timecourse without manual correction.
- Linear models (ridge regression/SVM) are sufficient to capture the semantic structure of narrative memories when combined with pre-trained semantic feature extraction (e.g., BERT/CLIP); non-linear deep learning approaches are excluded to ensure CPU feasibility and interpretability.
- The fMRIPrep pipeline, when run on a GitHub Actions ubuntu-latest runner with 8 parallel workers, will complete preprocessing for a single subject within 2 hours, allowing the full 10-subject subset (A moderate amount of total work) to be processed within the 6-hour CI job limit (20h / 8 workers = 2.5h).
- The distinction between "encoding" and "recognition" in the dataset is clearly demarcated in the metadata, allowing for separate extraction of neural patterns for each phase.
- The Natural Stories dataset (ds000234) does NOT contain a free-recall phase; the analysis is scoped to "encoding vs. recognition" and "reinstatement" patterns.
- The hypothesis that plot points are more reliably reconstructed than character details (e.g., accuracy ≥ 55% vs. [deferred]) is a research hypothesis to be tested, not a fixed system requirement.