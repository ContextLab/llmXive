# Implementation Plan: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Branch**: `001-llmxive-vae-geometric-analysis` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-vae-geometric-analysis/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-vae-geometric-analysis/spec.md`

## Summary
This project validates the geometric disentanglement of the Qwen-Image-VAE-2.0 latent space on the OmniDoc-TokenBench dataset. The primary approach involves encoding text-only and image-only regions (extracted via ground-truth bounding boxes) into latent vectors, training a Linear SVM to test for linear separability (US-01), and performing vector arithmetic to swap text content while preserving layout (US-02). 

**Key Methodological Updates**:
1. **Triviality Check**: A 'Pixel-Only' baseline classifier is added using *unlabeled* crops to ensure separation is not due to trivial pixel statistics (texture/edges).
2. **Linearity Validation**: A consistency check for the 'text direction' vector is performed before arithmetic to verify the latent space is locally linear.
3. **Region Purity Filter**: Mixed modalities (IoU > 0.1) are explicitly excluded from the dataset.
4. **CPU Feasibility**: If the model fails on CPU, the 'CPU-First' hypothesis is formally REJECTED; the GPU escape hatch is only for demonstrating editing capability, not for validating CPU feasibility.
5. **Statistical Scope**: Bonferroni correction is applied *only* to separability p-values (Accuracy, F1); SSIM/Keypoint are evaluated against fixed thresholds (≥0.85, ≥0.80) without p-values.
6. **Baseline Comparison**: Layout preservation metrics (SSIM, Keypoint) are computed against the *Baseline Reconstruction* (original image encoded and decoded without arithmetic) as mandated by FR-006 and US-02.
7. **Runtime Power Analysis**: If the required N for Power ≥ 0.8 exceeds the 6-hour CPU runtime limit, the result is reported as "Inconclusive" rather than reducing N.

All computations are constrained to a CPU-first environment with limited vCPU and RAM resources. Statistical rigor is maintained via permutation tests and Bonferroni corrections for multiple comparisons.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only, version 2.2.0), `transformers` (4.40.0), `datasets` (2.18.0), `scikit-learn` (1.4.0), `opencv-python` (4.9.0), `paddlepaddle-cpu` (2.7.0), `paddleocr` (2.7.0), `scipy` (1.13.0), `statsmodels` (0.14.1), `pyyaml` (6.0.1)  
**Storage**: Local filesystem under `data/` (streamed from Hugging Face), `data/interim/` for latent vectors and images.  
**Testing**: `pytest` (contract tests for schema validation, unit tests for metric calculations).  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, ~7 GB RAM).  
**Project Type**: Computational Research / CLI Pipeline  
**Performance Goals**: ≤ 6 hours total runtime; < 60 seconds per image for editing operations.  
**Constraints**: No local GPU; memory usage < 7 GB; strict adherence to dataset ground-truth annotations; no synthetic data generation.  
**Scale/Scope**: Subset of OmniDoc-TokenBench (streamed or sampled to fit memory); N images determined by power analysis and runtime constraints.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Verified Dataset Source**: `https://huggingface.co/datasets/omnineura/Omni-Doc-1` (OmniDoc-TokenBench benchmark subset).
**Verified Model Source**: `Qwen/Qwen-Image-VAE-2.0` (Hugging Face).

## Constitution Check

*Gates determined based on `projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/.specify/memory/constitution.md`*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Plan mandates `requirements.txt` in `code/`, pinned seeds, and deterministic data streaming from verified URLs (`https://huggingface.co/datasets/omnineura/Omni-Doc-1`). |
| **II. Verified Accuracy** | PASS | All dataset URLs cited explicitly in the text. Model source cited (`Qwen/Qwen-Image-VAE-2.0` on Hugging Face). No hallucinated sources. |
| **III. Data Hygiene** | PASS | Plan defines checksumming of downloaded data; raw data is immutable; derivations are new files. |
| **IV. Single Source of Truth** | PASS | Metrics (SSIM, Keypoint, Accuracy) are computed by code and written to JSON; paper figures reference these JSON files. |
| **V. Versioning Discipline** | PASS | Artifacts (latent vectors, edited images) will carry content hashes in `data/` metadata. |
| **VI. Latent Space Geometric Integrity** | PASS | Plan explicitly uses ground-truth bounding boxes for region extraction, permutation tests for separability, a 'Triviality Check' to rule out pixel-based artifacts, and a 'Linearity Validation' step. |
| **VII. CPU-First Zero-Shot Editing Validation** | PASS | Plan prioritizes CPU inference; if VAE fails on CPU, the 'CPU-First' hypothesis is REJECTED, and the GPU fallback is only for demonstrating editing (with a note that CPU feasibility is invalid). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-vae-geometric-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Targets for Implementer (generated by Implementer)
│   ├── dataset.schema.yaml
│   ├── latent-vector.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/
├── code/
│   ├── requirements.txt       # Pinned dependencies
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_loader.py     # Handles HF dataset streaming
│   │   ├── vae_encoder.py     # Qwen-Image-VAE wrapper
│   │   ├── classifiers.py     # Linear SVM/Logistic Regression
│   │   ├── editing.py         # Vector arithmetic & decoding
│   │   ├── metrics.py         # SSIM, Keypoint, Permutation tests
│   │   └── main.py            # Orchestration
│   └── tests/
│       ├── test_metrics.py
│       └── test_schemas.py
├── data/
│   ├── raw/                   # Downloaded parquet (checksummed)
│   ├── interim/               # Latent vectors, cropped images
│   └── results/               # JSON metrics, plots
└── docs/                      # Paper drafts, reports
```

**Structure Decision**: The single-project structure is selected. All code resides in `code/src/` to ensure a unified environment for data loading, encoding, and analysis. The `data/` directory is split into `raw` (immutable), `interim` (derived), and `results` (final metrics) to enforce data hygiene and lineage tracking.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GPU Fallback Logic** | The spec assumes CPU feasibility, but VAEs can be memory-intensive. A fallback to a scaled-down Kaggle GPU run (N=100) is required if CPU OOM occurs. | A pure CPU-only plan risks failure if the model is too large; a pure GPU plan violates the "CPU-first" constraint and CI limits. The fallback is explicitly tied to US-02 Assumptions and is reproducible (fixed seed, N=100). |
| **Streaming Data Loader** | The full dataset may exceed RAM. Streaming is required to process the full dataset without loading it all into memory. | Loading the full dataset into memory would crash the 7 GB runner. |
| **Multiple Comparison Correction** | FR-009 requires Bonferroni correction for separability tests. | Ignoring this would inflate Type I errors, violating the "Methodological Rigor" panel requirement. |
| **Triviality Check** | To ensure separation is not due to trivial pixel statistics (texture/edges). | A classifier on raw pixels might trivially separate text vs. image, invalidating the latent space claim. |
| **Runtime Power Analysis** | To ensure N is achievable within 6 hours on CPU. | If runtime > 6 hours, statistical power < 0.8, rendering the result "inconclusive". |

## Compute Feasibility & Decision Rationale

### CPU-First Strategy
- **Method**: `torch` CPU, `scikit-learn`, `opencv`, `paddlepaddle` (CPU wheel 2.7.0).
- **Justification**: The VAE encoder/decoder for document images is typically a convolutional network (U-Net or similar) which can run on CPU for small batches or single images. The classification (Linear SVM) is trivial on CPU. PaddleOCR (CPU wheel) is <1GB and fits within 7 GB RAM.
- **Memory Accounting**: VAE (~3GB) + PaddleOCR (~1GB) + OS/Data (~2GB) < 7GB. The CPU-only wheel is used to minimize overhead.
- **Risk Mitigation**: 
  1. **Model Availability Check**: Verify 'Qwen/Qwen-Image-VAE-2.0' exists and fits CPU before proceeding. If not, report 'Model Unavailable'.
  2. **Runtime Power Analysis**: Estimate runtime per image. If max N (within 6h) < required N for power, report 'Inconclusive'.
  3. **GPU Escape Hatch**: If CPU fails (OOM), the 'CPU-First Feasibility' hypothesis is REJECTED. A scaled-down run (N=100) on Kaggle GPU is performed only to demonstrate editing capability, with a note that the CPU feasibility claim is invalid.

### GPU Escape Hatch
- **Condition**: Only if `ImportError` or `OOM` on CPU.
- **Configuration**: Kaggle GPU (T4/P100), `device="cuda"`, `load_in_8bit` if applicable.
- **Scale**: Run on a subset of N=100 images (as per US-02 Assumptions) to demonstrate feasibility within the 9-hour kernel limit.
- **Reproducibility**: The N=100 subset is fixed-seed (seed=42) and documented in the output.

## Data Availability

- **Primary Dataset**: OmniDoc-TokenBench (Verified URL: `https://huggingface.co/datasets/omnineura/Omni-Doc-1`).
- **Access Strategy**: Use `datasets.load_dataset(..., streaming=True)` to iterate over the dataset without loading the entire file into RAM.
- **Verification Step**: Before processing, verify the presence of 'modality' and 'bbox' fields. If missing, report 'Data Unavailable'.
- **Region Purity Filter**: Exclude bounding boxes where text and image overlap (IoU > 0.1) or where OCR confidence is low.

## Methodology & Statistical Rigor

### 1. Data Loading & Preprocessing
- Stream the dataset.
- **Verification**: Confirm 'modality' and 'bbox' fields exist.
- **Filtering**: Exclude mixed regions (IoU > 0.1).
- **Power Analysis**: Calculate required N for Power ≥ 0.8.
- **Runtime Analysis**: Estimate runtime per image. If max N (within 6h) < required N, report 'Inconclusive'.

### 2. Latent Extraction (FR-003)
- Load Qwen-Image-VAE-2.0 encoder (Source: Hugging Face).
- Encode cropped regions.
- **CPU Constraint**: Attempt loading on CPU. If OOM, trigger 'Model Unavailable' or GPU escape hatch (with hypothesis rejection).

### 3. Disentanglement Analysis (US-01)
- **Triviality Check**: Train a 'Pixel-Only' classifier (raw pixels or edge density) on a *separate* set of unlabeled crops (or the same unlabeled set) to establish a baseline. If baseline accuracy > 90%, flag result as 'Trivial'. Labels are used *only* for evaluation.
- **Classifier**: Linear SVM (`sklearn.svm.LinearSVC`).
- **Training**: Train on a split of the latent vectors. Labels are ground-truth modality.
- **Evaluation**: Accuracy, F1-Score.
- **Permutation Test**: Shuffle labels multiple times to generate a null distribution. Calculate p-value.
- **Multiple Comparison Correction**: Apply Bonferroni correction to the p-values of Accuracy and F1 (separability tests only). SSIM and Keypoint are evaluated against thresholds, not p-values.

### 4. Vector Arithmetic & Editing (US-02)
- **Linearity Validation**: Test consistency of 'text direction' vector across multiple pairs.
- Compute centroids: $\mu_{text} = \text{mean}(Z_{text})$, $\mu_{image} = \text{mean}(Z_{image})$.
- Operation: $z_{edited} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$.
- Decode $z_{edited}$.
- **Metrics**:
  - **OCR Verification**: Confirm text content changed (≥95% accuracy) *before* assessing layout.
  - **Masked SSIM**: Compare edited image vs. **Baseline Reconstruction** (original image encoded and decoded without arithmetic) for non-text regions; result ≥ 0.85.
  - **Edge Alignment Score (EAS)**: Detect SIFT/ORB keypoints in non-text regions; match between edited and baseline; score ≥ 0.80.

### 5. Sensitivity Analysis (US-03)
- Sweep classification threshold around the decision boundary.
- Report False Positive Rate (FPR) and False Negative Rate (FNR) variations.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailable** | Fatal | Fallback to a smaller local sample if provided; otherwise, report "Data Unavailable". |
| **Model Unavailable** | Fatal | If 'Qwen/Qwen-Image-VAE-2.0' is not found or too large for CPU, report "Model Unavailable". |
| **Ambiguous Regions** | Medium | Exclude regions where text/image overlap significantly (IoU > 0.1) or flag for manual review. |
| **CPU OOM** | High | Trigger GPU escape hatch (N=100) but mark 'CPU-First Feasibility' as REJECTED. |
| **Low Statistical Power** | Medium | Report "Inconclusive" with the specific power value (SC-001). |
| **Runtime Exceeds 6h** | Medium | Report "Inconclusive" due to hardware constraints. |

## Output Contract

The implementation must produce:
1. `data/results/metrics.json`: Contains Accuracy, F1, SSIM, EAS, Permutation p-values, Bonferroni-corrected p-values (separability only), and 'triviality_flag'.
2. `data/results/plots/`: PCA visualizations, edited image examples.
3. `data/results/power_analysis.json`: Achieved power, effect size, status (conclusive/inconclusive).
4. `data/results/runtime_analysis.json`: Runtime per image, max N achievable.
