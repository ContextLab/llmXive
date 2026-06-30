# Research: Reproduce & Validate SpatialClaw (CPU Feasibility)

## Dataset Strategy

The primary dataset for this feasibility study is **BLINK**, but specifically the **Spatial** or **Diagram** subsets which contain explicit spatial reasoning tasks. The previous selection of `Art_Style` was identified as a mismatch for "spatial reasoning" validation.

| Dataset | Source URL | Access Method | Variable Fit Check | Status |
|:--- |:--- |:--- |:--- |:--- |
| **BLINK (Spatial/Diagram)** | `https://huggingface.co/datasets/BLINK-Benchmark/BLINK` (Filtered) | `datasets.load_dataset("parquet", data_files=...)` | **Verified**: Contains image paths and spatial relationship questions (e.g., "Where is X relative to Y?"). | **Selected** |
| **BLINK (Art_Style)** | ` | `datasets.load_dataset("parquet", data_files=...)` | **Rejected**: Contains style classification tasks, not spatial reasoning. | **Excluded** |
| **GQA** | ` | `datasets.load_dataset("gqa")` | **Fallback**: Contains explicit spatial questions. Used if BLINK spatial subset is unavailable. | **Fallback** |

**Note on Dataset Fit**: The `BLINK` dataset must be filtered to a subset containing spatial tasks. The plan **requires** the dataset to contain ground truth answers for spatial relationships. If the dataset lacks these (e.g., only style classification), the run will abort with "Dataset Mismatch: No spatial tasks found".

## Model Strategy

The paper utilizes large Vision-Language Models (VLMs) which are incompatible with the limited RAM CPU-only constraint.
- **Primary Target**: `microsoft/Phi-3-vision-128k-instruct` (quantized to 4-bit if necessary, but verified to run on CPU within 7GB) or `llava-hf/llava-1.5-7b-hf` (CPU-optimized).
- **Constraint**: Large models (e.g., LLaVA, Gemma) will likely require substantial RAM.
- **Rationale**: The plan explicitly selects a **CPU-tractable VLM** that supports image input.
- **Decision**: If the paper's specific model (e.g., LLaVA-13B) is required but cannot run on CPU, the system will **abort** with "Model Mismatch: Required model not CPU-tractable". No silent fallback to a text-only model (like Gemma-2b-it) is permitted as it lacks vision capabilities.
- **Rejection of Text-Only Models**: Models such as `gemma-2b-it` or `gemma-4-26b` (if text-only) are explicitly rejected for this task as they cannot process the image inputs required by the `BLINK` dataset.

## Statistical & Validation Strategy

### Ground Truth Validation (Revised)
The plan **removes** the comparison of subset accuracy to the paper's global average ([deferred]) as this is statistically invalid for small subsets (n=5) and construct-invalid (different model).
- **Logic**: Accuracy is calculated as `(Correct Answers / Total Samples)` against the **ground truth labels** provided in the dataset.
- **Statistical Note**: For small subsets (n=5), the result is a "Feasibility Check" only. No statistical inference (p-values, confidence intervals) is claimed. The report will explicitly state "Low Sample Size: Results are indicative only".
- **Success Metric**: The run is "Valid" if the agent produces executable code and an answer for >80% of samples. Accuracy is reported as a raw metric, not a pass/fail against a paper baseline.
- **Tolerance Removal**: The fixed ±5% tolerance is removed. Validation is based on resource compliance and execution success, not statistical deviation from a paper baseline.

### Resource Monitoring
- **Peak RAM**: Monitored via `psutil`. If `> 7000 MB`, abort immediately.
- **CPU Time**: Monitored via `time` module or `psutil`. If `> 21600 s`, abort.
- **GPU Check**: On startup, check `torch.cuda.is_available()`. If `True` (unexpected on CI) or if `CUDA_VISIBLE_DEVICES` is set, proceed. If `False` and code attempts to allocate CUDA tensors, catch the exception and raise `RuntimeError: GPU not available; aborting`.

## Risks & Mitigations

1. **Risk**: Dataset download fails or is incomplete.
 * **Mitigation**: Implement retry logic with exponential backoff. If all fail, exit with code 1 and specific error message.
2. **Risk**: VLM returns non-executable code.
 * **Mitigation**: The kernel wrapper must catch `SyntaxError`. Log the failure, attempt reflection (if configured), or skip and mark as "unanswerable".
3. **Risk**: Memory overflow on 7GB limit.
 * **Mitigation**: Process data in batches. If a single batch exceeds limit, reduce batch size dynamically or fail with "Memory Limit Exceeded".
4. **Risk**: Paper metrics vs. Subset metrics mismatch.
 * **Mitigation**: **Removed**. The plan no longer compares to paper metrics. It reports ground truth accuracy and flags "Low Sample Size" if n < 30.