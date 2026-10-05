# Data Model: Neural Narrative Networks

## Overview

This document defines the data schemas, storage formats, and transformation logic for the Neural Narrative Networks project. All data artifacts are stored under `data/` and processed according to the pipeline defined in `plan.md`.

## Data Flow

1. **Raw Ingestion**: Download OpenNeuro (fMRI) and ROCStories (text) from verified URLs.
2. **Preprocessing**: 
   - Extract ROI timecourses (Left Hipp, Right Hipp, DLPFC) using Harvard-Oxford masks (threshold 25%) or coordinate fallback.
   - **HRF-Aligned Extraction**: Apply a Finite Impulse Response (FIR) model to deconvolve the BOLD signal, addressing hemodynamic lag.
   - Align text events with fMRI timepoints based on the *intersection* of shared stories.
3. **Model Input**: Tokenized stories (exact fMRI stimuli) and event boundaries.
4. **Model Output**: Hidden state vectors for each story event.
5. **Analysis**: RSA matrices and p-values.

## Entity Definitions

### Neural Timecourse
- **Description**: A matrix of BOLD signal values over time for a specific ROI, deconvolved using FIR.
- **Source**: OpenNeuro ds001495.
- **Format**: `.npy` (NumPy array).
- **Shape**: `(N_subjects, N_timepoints)`.
- **Validation**: Check for NaNs, ensure non-zero variance.

### Narrative Representation
- **Description**: A vector of hidden state activations from the model.
- **Source**: SAE or TinyLSTM generator.
- **Format**: `.npy` or `.pt`.
- **Shape**: `(N_stories, N_events, Hidden_Dim)`.
- **Validation**: Ensure sparsity ratio ≤ 0.20 for SAE.

### RSA Matrix
- **Description**: A symmetric matrix of pairwise similarities between representations.
- **Source**: `code/analysis/rsa_computation.py`.
- **Format**: `.csv`.
- **Shape**: `(N_conditions, N_conditions)`.
- **Validation**: Symmetry check, diagonal = 1.

## Storage Schema

```text
data/
├── raw/
│   ├── openneuro/
│   │   ├── test-00000-of-00016.parquet  # Raw fMRI data
│   │   └── dataset_dict.json            # Metadata
│   └── rocstories/
│       ├── train-00000-of-00001.parquet # Raw text data
│       └── ROCStories__spring2016.csv   # Alternative format
├── processed/
│   ├── neural/
│   │   ├── roi_left_hipp.npy            # Left Hippocampus timecourses (HRF-aligned)
│   │   ├── roi_right_hipp.npy           # Right Hippocampus timecourses (HRF-aligned)
│   │   └── roi_dlpfc.npy                # DLPFC timecourses (HRF-aligned)
│   └── text/
│       └── rocstories_sample.jsonl      # Sampled stories with event boundaries (shared stimuli)
└── analysis/
    ├── rsa_matrices/
    │   ├── sae_rsm.csv                  # SAE Representational Similarity Matrix
    │   └── baseline_rsm.csv             # Baseline RSM
    └── results/
        └── permutation_test_results.csv # P-values and convergence stats
```

## Transformation Logic

### Preprocessing (Neural)
1. Load `test-00000-of-00016.parquet`.
2. Identify subjects with valid story conditions.
3. Apply Harvard-Oxford mask for Left Hippocampus (threshold 25%, linear registration to MNI).
4. **HRF-Aligned Extraction**: Apply FIR model to deconvolve BOLD signal.
5. Save to `roi_left_hipp.npy`.

### Preprocessing (Text)
1. Load `train-00000-of-00001.parquet`.
2. **Fallback**: Infer event boundaries via NLTK if missing.
3. Filter to the set of stories that match the fMRI stimuli (intersection).
4. Save to `rocstories_sample.jsonl`.

### RSA Computation
1. Load `roi_left_hipp.npy` and `sae_hidden_states.npy`.
2. Compute pairwise correlation for each condition.
3. Store in `sae_rsm.csv`.
