# Research: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

## Research Question

Does the structural consistency (geometric relation accuracy) of PerceptionDLM degrade non-linearly as the number of processed regions exceeds the native context window (20–50 regions), and at what point does the efficiency of parallelism become outweighed by this "consistency tax"?

## Dataset Strategy

### Source Data
The project relies on the **COCO-Stuff** dataset as the base for synthetic generation.
*   **Dataset Name**: COCO-Stuff (COCO + Stuff annotations)
*   **Verified Source**: `https://huggingface.co/datasets/psv/coco-stuff` (Verified via HuggingFace `datasets` library).
*   **Action**: The `synthetic/generator.py` will load images from `psv/coco-stuff` via `datasets.load_dataset("psv/coco-stuff")`.
*   **Constraint**: The dataset contains images and segmentation masks. We will use the images. The segmentation masks will be ignored for the baseline (as we generate our own regions).
*   **Variable Fit**: The verified dataset contains images. We will use the images. The "ground truth" relations will be **synthetically derived** from the geometric centroids of the generated boxes (Assumption in spec), as the dataset lacks specific relational labels for arbitrary box placements.

### Synthetic Generation Logic
1.  **Input**: Images from COCO-Stuff.
2.  **Process**: Randomly place $N$ bounding boxes ($N \in \{20, 30, 50\}$) ensuring non-overlap.
3.  **Output**: `synthetic_image.png` + `annotation.json` (coordinates).
4.  **Validation**: `validator.py` ensures no overlaps. If placement fails (e.g., small image), retry with reduced $N$ or skip.

## Methodology

### Phase 1: Synthetic Data Construction
*   **Goal**: Create 150 test samples (50 images × 3 region counts: varying low, medium, and high).
*   **Method**:
    *   Load base images from COCO-Stuff.
    *   Iteratively place boxes using a rejection sampling algorithm (random position/size -> check overlap -> accept/reject).
    *   Derive "Ground Truth Relations": For every pair of boxes $(A, B)$, compute spatial relation (e.g., "A is left of B" if $center_x(A) < center_x(B)$).
    *   Store relations in `annotation.json`.
    *   **Fallback**: If memory/time limits are approached, reduce sample size per bin to 20 (total 60) to ensure completion.

### Phase 2: Inference Execution
*   **Parallel Mode**:
    *   Load PerceptionDLM (CPU-compatible weights).
    *   Process regions in batches of a fixed size.
    *   **Constraint**: No cross-batch context (simulating fragmentation).
    *   Output: Captions per region.
*   **Sequential Mode**:
    *   Load PerceptionDLM (SAME model weights).
    *   Process regions one-by-one.
    *   **Constraint**: Context is RESET between regions (no accumulation) to match the fragmented state of the parallel batch. This isolates the "parallelism mechanism" rather than context window size differences.
    *   Output: Captions per region.

### Phase 3: Metric Calculation
*   **Geometric Consistency Score**:
    *   Extract spatial prepositions from generated captions using `spaCy`.
    *   Compare against derived ground-truth relations.
    *   Formula: $Score = \frac{\text{Matches}}{\text{Total Relations}}$.
    *   **Limitation**: This metric measures the model's ability to reproduce the geometric layout defined by the boxes. It does not measure high-level semantic understanding of the image content (e.g., "cat" vs "dog"). It is a proxy for structural consistency.
*   **BLEU-4**: Standard n-gram overlap (using `sacrebleu` or `nltk`).
*   **Inference Time**: Measure wall-clock time for each method.

### Phase 4: Regression & Visualization
*   **Regression**: Fit a curve (e.g., exponential decay or polynomial) to Region Count vs. Geometric Consistency Score for both methods.
*   **Tipping Point**: Identify $N$ where $Score_{parallel} < 0.9 \times Score_{sequential}$ (deferred threshold).
*   **Pareto Frontier**: Plot Inference Time (x) vs. Consistency (y).

## Compute Feasibility & Constraints

*   **Hardware**: GitHub Actions Free Tier (multiple vCPU, ~7 GB RAM).
*   **Memory Management**:
    *   Models loaded in FP32/FP16 (no 8-bit).
    *   Batch size limited to 8.
    *   Images processed one by one (or small batches) to keep peak RSS < 7 GB.
    *   If memory pressure detected, reduce sample size per bin (n=20 instead of 50) to ensure completion within 6 hours.
*   **Runtime**:
    *   Target: < 6 hours total.
    *   Strategy: Parallel inference is faster but less coherent; sequential is slower. The bottleneck is likely the sequential baseline.
    *   Fallback: If PerceptionDLM is too slow, use a smaller distilled variant or reduce the number of sequential passes.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Mismatch** | COCO-Stuff not available/verified. | Use verified `psv/coco-stuff`; synthetic relations derived from geometry. |
| **Memory Overflow** | Model + Image + Context > 7 GB. | Process images sequentially; clear Python objects (`gc.collect()`). |
| **Timeout** | Sequential inference too slow for 150 samples. | Reduce sample size per bin dynamically (fallback to n=20). |
| **Metric Validity** | Geometric relations don't match human semantics. | Acknowledge in paper as "Geometric Consistency" proxy; explicitly state it measures structural consistency, not semantic coherence. |

## References

1.  **PerceptionDLM**: (Citation to be verified against primary source).
2.  **COCO-Stuff**: (Citation to be verified against primary source).
3.  **Verified Dataset**: `psv/coco-stuff` (HuggingFace).
4.  **spacy**: "Industrial-strength Natural Language Processing in Python."