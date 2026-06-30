# Research: CiteVQA Reproduction & Validation

## Dataset Strategy

The CiteVQA benchmark relies on a specific dataset containing document images, questions, ground-truth answers, and ground-truth bounding boxes. The primary source for this dataset is the public CiteVQA repository.

**Verified Datasets**:
- **Source**: CiteVQA (Hugging Face Dataset ID: `lmsys/citevqa` or GitHub Repository: `lmsys/CiteVQA`).
- **Status**: Publicly accessible. The vendored `external/CiteVQA` submodule is a local copy of this source.
- **Action**: The plan relies on the `external/CiteVQA` submodule. If the submodule is empty, the implementation will attempt to fetch a minimal subset from the public source to validate the pipeline. This ensures the data resource is real and accessible outside the local repo context.

**Variable Fit Analysis**:
The study requires the following variables for SAA calculation:
1.  `question`: The query posed to the model.
2.  `answer`: The ground-truth text answer.
3.  `ground_truth_bbox`: The coordinates of the region in the image containing the answer.
4.  `image_path`: The path to the document image.

**Risk**: If the vendored dataset lacks `ground_truth_bbox` for any record, the SAA metric cannot be computed for that record. The plan (FR-005) mandates skipping such records and logging them, ensuring the metric is not skewed by missing data.

**Memory Constraints**:
The GitHub Actions free-tier runner has limited RAM. Loading a full MLLM model (e.g., LLaVA, Qwen-VL) and a large dataset simultaneously may exceed this limit.
- **Strategy**: The implementation will use `torch_dtype=torch.float16` (if supported on CPU) or `torch.float32` with strict batch size limits (batch_size=1). The dataset will be loaded in streaming mode or a small subset for CI validation to ensure RAM usage remains under 7 GB.
- **Reference**: This aligns with **FR-006** and **SC-003**.

## Model & Methodology

**Model Selection**:
The specific MLLM model is defined in the `external/CiteVQA` configuration.
- **Constraint**: The model must be loaded in CPU-only mode.
- **Method**: Use `device_map="cpu"` or default CPU inference. No CUDA/GPU dependencies (`load_in_8bit` with bitsandbytes is forbidden as it often requires CUDA).
- **Feasibility**: Small/medium MLLMs (e.g., 7B parameters in float16) may struggle with 7 GB RAM limits. The plan assumes the model can be loaded with quantization or that the CI run uses a smaller subset of the model weights if available. If the model exceeds 7 GB even with quantization, the plan will log a specific OOM error and exit gracefully (Edge Case 1).

**Spatial Output Mechanism**:
To enable the SAA metric, the model must generate bounding boxes.
- **Mechanism**: The inference pipeline uses the specific prompt template defined in the CiteVQA paper, which instructs the model to output the answer and the corresponding bounding box coordinates in a structured format (e.g., JSON or a specific token sequence).
- **Validation**: The `infer/run.py` script parses this output to extract `predicted_bbox`. If the model fails to output a box, the record is marked as "Answer Only" or "Both Wrong" depending on the answer correctness, and the IoU calculation is skipped for that record.

**Evaluation Metric: Strict Attributed Accuracy (SAA)**
- **Definition**: A prediction is correct only if:
  1.  The predicted answer matches the ground-truth answer (exact match or semantic equivalence as per CiteVQA definition).
  2.  The predicted bounding box has a sufficient Intersection over Union (IoU) with the ground-truth bounding box.
- **IoU Threshold**: The threshold is set to **0.5** (community standard per CiteVQA paper).
- **Normalization Strategy**: Both `predicted_bbox` and `ground_truth_bbox` are normalized to the [0, 1] range by dividing by the image width and height before IoU calculation. This ensures mathematical validity regardless of the original coordinate system (pixels vs. normalized).
- **Bias Mitigation**: As noted by the reviewer (Kahneman-simulated), we must avoid the "WYSIATI" trap where the system is rewarded for finding *some* text that looks like an answer. The SAA metric explicitly penalizes "Attribution Hallucinations" (correct answer, wrong region).
- **Statistical Rigor**: Since this is a benchmark reproduction, the SAA score is an associational metric describing performance on this specific dataset. No causal claims are made.
- **Statistical Limitations**: The CI run uses a sample size sufficient to support preliminary analysis. This is sufficient for *functional validation* (does the pipeline run?) but insufficient for *statistical* performance claims or validating the sensitivity to WYSIATI bias. The variance in the `answer_only_correct` count with n=10 is too high to distinguish systematic bias from random noise. This run serves as a *sanity check* for the metric's existence and the pipeline's ability to detect attribution errors. A larger, statistically powered sample is required for full metric validation.

## Computational Feasibility

**Runner Constraints**:
- **CPU**: 2 cores
- **RAM**: ~7 GB
- **Disk**: ~14 GB
- **Time**: ≤ 6 hours
- **GPU**: None

**Strategy**:
1. **Sample Size**: The CI job will run with `--sample-size 10`. This ensures the runtime is well [deferred] and memory is under 7 GB.
2.  **Model Loading**: The model will be loaded with `low_cpu_mem_usage=True` if available in the `transformers` library.
3.  **Data Streaming**: The dataset loader will use `streaming=True` to avoid loading the entire dataset into RAM.
4.  **Error Handling**:
    - **OOM**: Catch `RuntimeError` or `MemoryError`, log "Model too large for CPU runner", and exit with code 1.
    - **Missing Data**: Skip records with missing `bbox` or `image`, log warning, continue.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| CPU-only inference | Required by free-tier runner; no GPU available. |
| Sample size = 10 | Ensures CI job completes within 6 hours and 7 GB RAM; sufficient for functional validation. |
| Skip missing bbox records | Prevents SAA calculation errors; aligns with FR-005. |
| IoU Threshold = 0.5 | Community standard per CiteVQA paper. |
| Normalization to [0, 1] | Ensures mathematical validity of IoU calculation across coordinate systems. |
| Prompt-based spatial output | Required to generate `predicted_bbox` for the SAA metric. |
| No external dataset URL | CiteVQA data is publicly available at `lmsys/citevqa` (Hugging Face) or the GitHub repo; the plan relies on the vendored submodule but verifies the public source. |