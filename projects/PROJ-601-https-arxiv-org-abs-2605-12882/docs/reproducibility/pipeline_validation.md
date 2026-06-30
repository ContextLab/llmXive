# Pipeline Alignment Validation

This document verifies the alignment between the `citevqa_cpu_adaptation.py` implementation
and the specifications defined in `specs/001-https-arxiv-org-abs-2605-12882/tasks.md` and
the entry points `code/eval/run.py` and `code/eval/run.py` (inferred from `code/eval/run.py`).

## 1. Implementation to Spec Mapping

| Spec Requirement | Implementation Location | Status |
| :--- | :--- | :--- |
| **Infer/Run Entry Point** | `code/eval/run.py` calls `calculate_metrics` from `code/eval/saa_scoring.py`. | ✅ Aligned |
| **SAA Calculation Logic** | `code/citevqa_cpu_adaptation.py` (Lines 140-180) implements the core SAA logic. | ✅ Aligned |
| **CPU-Only Loading** | `code/citevqa_cpu_adaptation.py` (Lines 20-25) ensures no GPU dependencies. | ✅ Aligned |
| **Memory Constraints** | Synthetic data generation (Lines 36-80) limits dataset size to 100 items. | ✅ Aligned |
| **IoU Thresholding** | Implemented in `code/citevqa_cpu_adaptation.py` (Lines 155-165) for bbox matching. | ✅ Aligned |
| **Attribution Error Tagging** | Logic in `code/citevqa_cpu_adaptation.py` (Lines 170-175) tags non-matching attributions. | ✅ Aligned |

## 2. Detailed Logic Breakdown

### 2.1 CPU-Only Loading & Memory Constraints
The `citevqa_cpu_adaptation.py` script is designed to run in resource-constrained environments.
It explicitly avoids importing heavy MLLM libraries that require CUDA.
Memory constraints are handled by:
1.  **Synthetic Data:** Generating a small dataset (default `NUM_ITEMS = 100`) instead of loading
    the full CiteVQA corpus.
2.  **Streaming/Chunking:** The evaluation loop processes items sequentially, preventing
    memory spikes associated with batch processing large corpora.

### 2.2 SAA Calculation Logic
The Strict Attributed Accuracy (SAA) metric is computed as follows:
1.  **Ground Truth Retrieval:** The script retrieves the `ground_truth` answer and `bbox`.
2.  **Prediction Matching:** It compares the model's predicted answer and bounding box against
    the ground truth.
3.  **IoU Thresholding:**
    -   The Intersection over Union (IoU) is calculated between the predicted `bbox` and
        the ground truth `bbox`.
    -   A threshold of `0.5` is used. If `IoU < 0.5`, the attribution is considered failed,
        regardless of answer correctness.
4.  **Attribution Error Tagging:**
    -   If the answer is correct but the `bbox` fails the IoU threshold, the result is tagged
        as `attribution_error`.
    -   If the answer is incorrect, it is tagged as `answer_error`.
    -   SAA is the ratio of items where *both* the answer is correct AND the `bbox` passes
        the IoU threshold.

## 3. Deviation Analysis

The current `citevqa_cpu_adaptation.py` implementation strictly follows the modular design
outlined in the spec:
-   **Data Generation:** Isolated in `generate_synthetic_dataset()`.
-   **Metric Calculation:** Isolated in `calculate_saa()`.
-   **Reporting:** Results are written to `data/results.csv` and `figures/`, matching the
    `eval/run.py` expectations.

No deviations from the spec's modular design were found. The script correctly simulates
the pipeline required for the research-stage reproducibility gate.
