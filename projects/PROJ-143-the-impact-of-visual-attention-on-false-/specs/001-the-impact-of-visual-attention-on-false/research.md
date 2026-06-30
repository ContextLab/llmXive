# Research: The Impact of Visual Attention on False Memory Formation

## Executive Summary

This research investigates whether visual attention to salient but irrelevant objects is **associated** with false memory formation. The study leverages the Visual Genome dataset for stimuli and ground-truth object annotations, combined with human recall transcripts (hypothetical or sourced from OpenNeuro ds003166 if alignment is confirmed). A CPU-compatible deep visual attention model generates saliency maps, which are correlated with false-memory flags. The analysis includes robustness checks and adheres to strict computational constraints (CPU-only, <7 GB RAM).

**Critical Finding**: The study is currently **blocked** due to the lack of verified dataset sources for Visual Genome, SALICON, and OpenNeuro.

## Dataset Strategy

| Dataset | Source URL | Usage | Verification Status |
|---------|------------|-------|---------------------|
| Visual Genome (Images & Annotations) | *NO verified source found in block* | Primary stimuli and ground-truth object presence. | **Critical Gap**: The provided "# Verified datasets" block does **not** list a verified URL for Visual Genome. The spec assumes Visual Genome exists. **Action**: The implementation must handle this gap by either (a) using a verified alternative if available in the block (none listed), or (b) explicitly stating in the pipeline that Visual Genome is unverified and proceeding with caution, or (c) halting if the constitution requires verified sources for all datasets. Given the block says "NO verified source found", the plan must **not** fabricate a URL. The pipeline will attempt to load from a standard local path or public mirror, but the lack of a verified URL is a blocking risk for "Verified Accuracy" (Constitution Principle II). |
| SALICON (Saliency Benchmark) | *NO verified source found in block* | Validation of the saliency model (FR-003). | **Critical Gap**: Same as above. No verified URL in the block. The plan cannot cite a URL. The model validation must be performed on a local copy or a standard benchmark loader if available, but the lack of a verified source is a risk. |
| Memory-for-Scenes / OpenNeuro ds003166 | *NO verified source found in block* | Human recall transcripts for false-memory coding. | **Critical Gap**: No verified URL. The spec assumes alignment with Visual Genome IDs. The plan must explicitly state that the alignment protocol (FR-011) cannot be verified without a confirmed dataset source. |

> **Critical Note on Dataset Availability**: The "# Verified datasets" block provided in the user message lists only `us_100K_difficult` and `us_100K_easy` (which appear unrelated to Visual Genome or memory recall) and marks Visual Genome, SALICON, and OpenNeuro as having **NO verified source**. **This is a fatal flaw for the current plan.** The implementation **cannot** proceed with a dataset that lacks a verified source if the constitution requires "Verified Accuracy" (Principle II). 
>
> **Decision**: The plan will proceed **only if** the implementation includes a fallback mechanism to use a verified dataset (e.g., a subset of a verified dataset that contains similar stimuli) or if the user provides a verified URL. As written, the plan **cannot** satisfy FR-001 (download Visual Genome) or FR-003 (validate on SALICON) with a verified URL. The `research.md` will document this gap and propose a **CPU-tractable simulation** using the `us_100K` datasets (if they contain images) or a synthetic dataset, but this deviates from the spec. 
>
> **Revised Strategy**: Since the spec explicitly requires Visual Genome and the block says "NO verified source", the plan must **flag this as a blocking gap** and propose an alternative: **Use a verified subset of a similar dataset (e.g., COCO) if available in the block, or simulate the data generation process using the `us_100K` datasets if they contain images.** However, the `us_100K` datasets appear to be transaction logs, not images. 
>
> **Final Decision**: The plan will **halt** at the research phase until a verified dataset source is provided. For the purpose of this plan, we will assume the user will provide a verified URL for Visual Genome and SALICON, or the project will be re-scoped to use a verified dataset (e.g., a subset of COCO if available). **The plan below assumes the user will provide a verified URL for Visual Genome and SALICON.** If not, the project cannot proceed.

**Dataset Incompatibility Note**: OpenNeuro ds003166 uses specific, curated scene stimuli, not the full Visual Genome corpus. There is no mechanism to map Visual Genome IDs to the specific stimuli used in ds003166. Without a shared stimulus set, the dependent variable (recall) and independent variable (saliency of VG image) are unlinked, rendering the correlation analysis impossible.

## Methodology

### 1. Data Acquisition & Preprocessing
- **Visual Genome**: Download images and region annotations. Filter for images with valid object masks.
- **Recall Transcripts**: Align with Visual Genome IDs using FR-011 protocol. Exclude mismatches.
- **Saliency Model**: Load a pre-trained CPU-compatible model (e.g., `torch` with `cpu` device). Generate fixation maps for each image.

### 2. False Memory Coding (FR-005)
- For each object in an image:
  - Check if it appears in the recall transcript.
  - Check if it is absent from Visual Genome ground truth.
  - Apply secondary verification (e.g., manual spot-check or consensus) to rule out unannotated valid objects.
  - Flag as false memory if (a), (b), and (c) are met.

### 3. Statistical Analysis
- **Primary Test**: Pearson correlation (r) between object saliency and false-memory rate (aggregated across participants).
- **Secondary Test**: Mixed-effects logistic regression with random intercepts for participants and items.
- **Correction**: Benjamini-Hochberg FDR for item-wise tests (FR-008).
- **Robustness**: Sensitivity analysis over percentile thresholds (5%, 10%, 15%) and alternative saliency models (ViT-B/16 CAM).

### 4. Power Analysis (FR-010)
- Target: Detect r = 0.30 with 80% power, α = 0.01.
- Calculate required sample size. If the dataset is insufficient, document the shortfall (SC-005).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Benjamini-Hochberg FDR correction applied to item-wise tests.
- **Sample Size**: Power analysis performed a priori. If the dataset is too small, the study is underpowered, and this will be reported.
- **Causal Inference**: The study is **observational**. Claims will be framed as associational, not causal. No randomization or identification strategy is used.
- **Measurement Validity**: The saliency model is validated on SALICON (if a verified source is provided). If not, the validity is assumed based on literature.
- **Collinearity**: Saliency scores and false-memory rates may be correlated with other factors (e.g., object size, category). These will be reported descriptively, and collinearity will be acknowledged.
- **Annotation Error**: The "false memory" label may be confounded by Visual Genome annotation incompleteness. The analysis will control for this by testing the correlation between saliency and annotation density.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM, 6 h).
- **Model**: CPU-compatible saliency model (no GPU, no quantization).
- **Data**: Sampled to **50 images** to fit memory and time constraints.
- **Libraries**: `torch` (CPU wheel), `scikit-learn`, `pandas`, `numpy`, `statsmodels`.
- **Image Size**: Downsampled to 224x224 before inference.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **No verified dataset source** | **Blocking Risk**: The plan cannot proceed without a verified URL for Visual Genome, SALICON, or OpenNeuro. The user must provide a verified URL or re-scope the project. |
| **Dataset mismatch** | If the dataset lacks required variables (e.g., recall transcripts), the study cannot be performed. The plan will document this gap. |
| **CPU performance** | Sample the dataset to fit memory and time constraints. Use efficient data structures. Downsample images. |
| **Ground-truth incompleteness** | SC-006: Report the rate of false positives due to Visual Genome incompleteness. If >10%, flag as "inconclusive". |
| **Dataset Incompatibility** | OpenNeuro and Visual Genome do not share IDs. The study is blocked until a verified recall dataset with VG IDs is found. |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **CPU-only model** | Required for GitHub Actions free-tier. |
| **Sampled dataset (50 images)** | To fit memory (7 GB) and time (6 h) constraints. |
| **FDR correction** | Required by FR-008 for multiple comparisons. |
| **Observational framing** | The study is correlational; no causal claims. |
| **Dataset gap** | **Blocking**: No verified source for Visual Genome, SALICON, or OpenNeuro. The plan assumes the user will provide a verified URL. If not, the project cannot proceed. |
| **Downsampling** | To fit memory and time constraints for CPU inference. |
| **Confounder control** | To reduce bias in the association estimate. |
| **Annotation error control** | To ensure the "false memory" signal is not just dataset noise. |
