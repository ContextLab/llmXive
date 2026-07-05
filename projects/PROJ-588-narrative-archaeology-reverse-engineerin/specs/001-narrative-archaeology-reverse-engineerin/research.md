# Research: Narrative Archaeology: Neural Pattern Classification and Reinstatement Analysis

## 1. Problem Statement

The project aims to determine if neural activity patterns during story listening (encoding) can be used to classify specific narrative elements (plot, characters, themes) and to test for neural pattern reinstatement (stability) within the encoding phase. This addresses the core question of how narrative information is represented and maintained in the brain during naturalistic listening. The scope is explicitly limited to *classification* of event types and *reinstatement* analysis, not generative text reconstruction.

## 2. Dataset Strategy

The primary dataset is **OpenNeuro ds000234** (Natural Stories).

**Verified Source**:
The dataset is accessed via the HuggingFace mirror of the OpenNeuro data, as verified in the project inputs:
- **URL**: ` (and associated arrow files).
- **Note**: The prompt explicitly lists this as a verified dataset source. The raw BIDS data will be downloaded via the OpenNeuro CLI or direct HTTP from the canonical source, but for the purpose of this plan, we rely on the verified HuggingFace mirror for the parquet/arrow data which contains the necessary fMRI data structure.

**Dataset Fit Analysis**:
- **Required Variables**: fMRI timecourses (BOLD), task labels (encoding), event onsets/durations, story text annotations.
- **Verification**: ds is a well-known naturalistic fMRI dataset containing a substantial number of subjects listening to a 16-minute story. It includes event annotations for semantic segmentation.
- **Gap Check**: The dataset does **not** contain a recognition/recall phase. The analysis is scoped to "Within-Session Pattern Stability" (early vs. late events) and "Event Segmentation" as per the spec's Assumptions and the dataset's actual content. The dataset contains sufficient temporal resolution for event-related analysis when convolved with HRF.

## 3. Methodological Approach

### 3.1 Data Ingestion & Preprocessing
1. **Download**: Fetch data for a 10-subject subset from the verified source.
2. **Preprocessing**: Run `nilearn`/`niworkflows` (CPU-optimized) to correct motion, normalize to MNI space, and smooth.
 - *Constraint*: Must complete 10 subjects in ≤6 hours on 2 vCPU.
 - *Strategy*: Parallelize across subjects. If a subject fails (motion artifacts), log and skip (Constitution Principle III).
 - *Adaptation*: Full fMRIPrep is replaced by a lightweight pipeline to meet the 2 vCPU constraint.
3. **Segmentation**: Map story event annotations (plot, character, theme) to fMRI timepoints. Apply HRF convolution to align event labels with the BOLD signal lag.

### 3.2 Within-Session Pattern Stability (RSA)
- **Method**: Representational Similarity Analysis (RSA).
- **Procedure**:
 1. Extract timecourses for ROIs: Hippocampus, mPFC, PCC, Lateral Temporal Cortex.
 2. Compute dissimilarity matrices for early-early, late-late, and early-late event pairs.
 3. **Hypothesis**: Early-late dissimilarity < Early-early (unrelated) dissimilarity, indicating pattern stability/reinstatement.
 4. **Null Model**: Compare against 'Early vs. Unrelated-Story' patterns to establish a baseline.
- **Significance**: Permutation testing (1000 iterations) with FDR correction (q < 0.05) across ROIs.

### 3.3 Narrative Element Classification (Decoding)
- **Method**: Linear Classifiers (Ridge Regression / SVM).
- **Features**: Semantic features extracted from story text using a pre-trained model (e.g., BERT-base) to map text to a semantic space.
- **Procedure**:
 1. Train model to predict event labels (plot, character, theme) from neural patterns.
 2. **Hypothesis**: Plot points are classified with higher accuracy than character details.
 3. **Baseline**: Compare against chance level (1/N, where N=20 for plot points, N=10 for characters) and a null distribution (shuffled labels).
 4. **Control**: Compare against a 'text-only' baseline model to disentangle semantic similarity from neural reinstatement.
 5. **Fallback**: If N=20 classification fails due to power, aggregate classes into broader categories (e.g., 'Action', 'Description') while reporting the N=20 attempt.
- **Correction**: Multiple-comparison correction (FDR) for testing across multiple categories and ROIs.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: FDR correction (Benjamini-Hochberg) applied to all ROI and category tests (explicitly mapping to FR-006 scope).
- **Power Analysis**: Sample size (N=10 subjects) is limited. Power is acknowledged as a limitation; results will be framed as "associational" and "preliminary" rather than definitive causal claims. A hierarchical aggregation strategy is in place for low-power classes.
- **Causal Inference**: Observational study. No randomization of story content. Claims are restricted to "neural correlates" and "associations."
- **Collinearity**: Semantic features (e.g., "character" and "plot" may share words) are collinear. The plan will report descriptive statistics for feature correlations and avoid claiming independent effects for highly correlated predictors.
- **Measurement Validity**: Relies on established `nilearn` pipelines and BERT embeddings for semantic validity.
- **Circularity Control**: Validation uses held-out data and cross-subject generalization to ensure the model is learning neural patterns, not just text-text correlations.

## 5. Compute Feasibility Plan

- **Hardware**: GitHub Actions Free Tier (multiple vCPU, substantial RAM).
- **Strategy**:
 - **Preprocessing**: Use `nilearn`/`niworkflows` (CPU-optimized) instead of full fMRIPrep Docker containers.
 - **Data**: Downsample fMRI data to standard isotropic resolution.
 - **Models**: Use `scikit-learn` linear models (CPU-optimized). No GPU tensors.
 - **Semantic Features**: Use a distilled BERT model or pre-computed embeddings if memory is tight.
 - **Runtime**: 10 subjects × [deferred] preprocessing = 5 hours. Decoding < 1 hour. Total < 6 hours.

## 6. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Subset of 10 subjects** | Required to meet 6-hour CI limit on 2 vCPU. Full dataset (30+ subjects) would exceed time/memory. |
| **Lightweight Preprocessing** | Full fMRIPrep is infeasible on 2 vCPU. `nilearn`/`niworkflows` is a validated, lighter alternative. |
| **Within-Session RSA** | ds000234 lacks a recognition phase. "Early vs. Late" analysis tests pattern stability within the encoding phase. |
| **Linear Models (Ridge/SVM)** | Deep learning is not feasible on CPU-only CI. Linear models are interpretable and sufficient for semantic mapping. |
| **HRF Convolution** | Essential to align discrete event labels with the slow BOLD signal (lag ~several seconds). |
| **FDR Correction** | Necessary to control family-wise error rate across multiple ROIs and narrative categories (FR-006). |
| **Dataset Source** | Strict adherence to verified HuggingFace/OpenNeuro links. No fabricated URLs. |
| **N=20/10 Targets** | Explicitly targeting N=20 (plot) and N=10 (character) as per SC-003, with hierarchical aggregation fallback. |
