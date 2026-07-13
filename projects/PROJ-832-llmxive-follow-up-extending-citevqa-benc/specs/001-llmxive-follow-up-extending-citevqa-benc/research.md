# Research: llmXive follow-up: extending "CiteVQA"

## Overview

This research phase investigates the capability of text-only language models to perform **evidence attribution** in document understanding tasks. While text-only models excel at reasoning, they lack the visual grounding required to map text spans to specific spatial coordinates (bounding boxes) on a document page. This project benchmarks this capability against the **Strict Attributed Accuracy (SAA)** metric, comparing text-only pipelines to a visual-only control (measured by **Visual Localization Accuracy**, VLA) and a fixed baseline from the original CiteVQA paper.

## Dataset Strategy

**CRITICAL BLOCKING GAP**: The project relies on the **CiteVQA** dataset, which must contain Query-Answer-Bounding Box triplets. The "Verified datasets" block provided in the user message **does not** contain a verified URL for CiteVQA.

Per Constitution Principle II (Verified Accuracy), the project **cannot proceed** without a verified source for the primary dataset. The plan explicitly rejects the use of proxy datasets (e.g., ICLR-pdfs + synthetic QA) because:
1. Synthetic QA pairs lack the ground-truth bounding box annotations required for the IoU calculation.
2. The SAA metric is uncomputable without verified boxes.
3. The "Attribution Hallucination" failure mode cannot be empirically tested on synthetic data.

**Strategy**:
1. **Primary**: Secure a verified URL for the CiteVQA dataset (e.g., via HuggingFace `datasets.load_dataset('citevqa')` if public, or a direct, verified download link).
2. **Fallback**: If no verified source is found, the project is **blocked** and will not proceed to implementation. No synthetic or unverified data will be used.

**Dataset Table**:

| Dataset Name | Purpose | Source URL (Verified) | Loading Method |
|:--- |:--- |:--- |:--- |
| **CiteVQA** | Primary QA + Bounding Box Data | **NO VERIFIED SOURCE** (Blocked) | `datasets.load_dataset('citevqa')` (if public) or manual fetch. *Status: BLOCKING.* |
| **ICLR-pdfs** | Document Layout / PDF Source | ` | `datasets.load_dataset` (Only for layout validation, not primary SAA) |
| **all-MiniLM-L6-v2 Embeddings** | Retriever Training/Validation | ` | `datasets.load_dataset` |
| **SAA Metrics** | Baseline Validation | ` | `datasets.load_dataset` |

> **Note**: The project is **blocked** until a verified source for CiteVQA is provided. The "ICLR-pdfs" dataset is listed only for potential layout validation but cannot replace CiteVQA for the SAA metric.

## Methodology

### 1. Text-Only Pipeline (US-1)
* **Retrieval**: Encode document chunks using `sentence-transformers/all-MiniLM-L6-v2`. Retrieve top-k (k=3) chunks for each query.
* **Reasoning**: Feed query + retrieved text to `Phi-3-mini` (instruction-tuned). Prompt model to output: `{"answer": "...", "chunk_id": "..."}`.
* **Constraint**: No image input. Model must rely solely on text.
* **Answer Correctness Check**: A predicted answer is considered correct **only if**:
 1. Exact Match OR Semantic Similarity (Cosine Similarity using `all-MiniLM-L6-v2` ≥ 0.85) **AND**
 2. The Ground Truth Answer is present in the *retrieved* top-k context.
 * *Rationale*: This prevents the model from "hallucinating" a correct answer from parametric knowledge without retrieving the evidence, ensuring the SAA metric truly measures attribution.

### 2. Spatial Grounding & SAA Calculation (US-2)
* **Mapping**: `chunk_id` -> `bounding_box` (from JSON metadata).
* **IoU Calculation**: Intersection over Union between predicted box and ground-truth box.
* **SAA**: `1` if (Answer Correct [Retrieval-Conditioned] AND IoU > 0.5), else `0`.

### 3. Visual-Only Control (US-3) - Visual Localization Accuracy (VLA)
* **Input**: Full-page image (cropped from PDF).
* **Model**: Vision-capable model (small, CPU-tractable).
* **Output**: Predicted bounding box (or chunk ID).
* **Metric**: **Visual Localization Accuracy (VLA)**.
 * VLA = `1` if IoU(Predicted Box, Ground Truth Box) > 0.5, else `0`.
 * *Note*: This metric is distinct from SAA. It tests the model's ability to *locate* the answer visually, without the text reasoning component. This isolates the modality gap.

### 4. Statistical Analysis (FR-007, SC-002)
* **Method**: **Bootstrap Confidence Interval (CI)**.
* **Procedure**:
 1. Calculate the mean SAA for the Text-Only pipeline.
 2. Generate 10,000 bootstrap samples of the SAA scores.
 3. Compute the 95% Confidence Interval (2.5th to 97.5th percentile) of the bootstrap distribution.
 4. Compare the Baseline Scalar (from CiteVQA paper) against this CI.
 5. **Significance**: If the Baseline Scalar falls *outside* the 95% CI, the difference is considered statistically significant (p < 0.05).
* *Rationale*: A one-sample t-test is invalid for comparing a sample against a fixed scalar from a different study. The Bootstrap CI correctly accounts for the variance in the new sample without assuming the baseline has zero variance.

## Feasibility & Compute Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 14GB Disk).
* **Model**: `Phi-3-mini` (16-bit or 8-bit CPU-supported inference).
* **Memory**: 7GB RAM is tight. We will process in batches and use `torch.no_grad()`.
* **Runtime**: 6 hours limit. We will sample the test set if the full set exceeds this.
* **Fallback**: If `Phi-3-mini` exceeds memory, we will switch to `TinyLlama` (documenting the trade-off).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **CiteVQA Dataset Unavailable** | Project Blocked | **Halt project**. No synthetic or proxy data will be used as they cannot support the SAA metric. |
| **OOM (Out of Memory)** | Job Failure | Use smaller model (TinyLlama), reduce batch size, or process single queries sequentially. |
| **Inference > 6h** | Job Timeout | Sample test set to 100-200 examples; parallelize if possible (limited by CPU). |
| **IoU Calculation Error** | Metric Invalid | Unit test IoU logic with known coordinates; validate against `SAA` parquet dataset. |
| **Bootstrap CI Convergence** | Statistical Invalidity | Ensure sufficient bootstrap samples (10,000) and check for convergence stability. |