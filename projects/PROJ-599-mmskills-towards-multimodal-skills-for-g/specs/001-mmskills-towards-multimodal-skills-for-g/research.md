# Research: MMSkills Reproduction & Validation

## 1. Research Objective
To validate the **Pipeline Robustness** and **Structural Integrity** of the MMSkills framework in a CPU-constrained environment. The primary goal is to confirm that the agent can parse skill packages (JSON + Images) from a verified dataset source, execute a small subset of tasks within the 6-hour CI limit, and correctly log errors (including missing assets and timeouts) without crashing.

**Scientific Limitations**: This study does **not** aim to replicate the paper's performance baselines or validate the "multimodal procedural knowledge" claim via performance comparison. The hardware (CPU vs GPU) and sample size (N=5) make such a comparison scientifically invalid. The success metric is strictly "Structural Execution Rate" (can the pipeline run without crashing?), not "Skill Acquisition" (does the agent solve the task as well as the paper?).

## 2. Dataset Strategy

The MMSkills framework relies on the **OSWorld** benchmark for evaluation. To ensure data integrity and reproducibility, we must use a verified dataset source.

**Verified Datasets**:
- **OSWorld Benchmark**: `https://huggingface.co/datasets/osworld/osworld` (Verified HuggingFace source).
- **MMSkills Skill Definitions**: Located within the `external/MMSkills` submodule (Code only) or a verified MMSkills release.

**Strategy**:
1.  **Source Separation**: The `external/MMSkills` submodule provides the code logic and skill definitions (JSON structures). The `osworld/osworld` HuggingFace dataset provides the binary assets (images, task metadata) *if* the task IDs match.
2.  **Data Fetching**: The `loader.py` script will fetch the specific task images and metadata from the verified HuggingFace `osworld/osworld` dataset.
3.  **Schema Compatibility Check**: Before execution, the plan mandates a pre-flight check:
    - Verify that the `osworld/osworld` dataset contains the specific task IDs referenced in the `external/MMSkills` skill definitions.
    - Verify that the data structure (e.g., `plan.json`, `state_cards.json`) matches the `skill_package.schema.yaml`.
    - If the dataset lacks required keys or the schema mismatch is detected, the `loader.py` must detect this and fail gracefully (Exit Code 3: "Data Schema Mismatch").
4.  **No Mock Data**: The plan **explicitly forbids** "Mock Benchmark" modes. If the verified dataset is unavailable or incompatible, the run must fail. This prevents construct validity failure where a mock environment validates a "skill" that doesn't exist.

*Action Item*: The Implementer must verify the contents of the `osworld/osworld` dataset during the `setup` phase. If the specific tasks required for the subset are missing, the plan defaults to a "Data Unavailable" state and exits with a clear error.

## 3. Methodology & Statistical Rigor

### 3.1. Execution Flow Validation (FR-001, FR-006)
*   **Method**: Install dependencies with `torch` pinned to the CPU-only wheel (`torch==2.1.0+cpu`).
*   **Verification**: The entry point script (`run.py`) will check `torch.cuda.is_available()`. If `False`, it will explicitly set `device="cpu"` for all model loads.
*   **Rigor**: This ensures the results are not influenced by GPU-specific optimizations or hardware availability, strictly adhering to the CI constraints.

### 3.2. Skill Loading & Integrity (FR-002, FR-007, SC-005)
*   **Method**: The `loader.py` will parse `plan.json`, `state_cards.json`, and `IMAGE_REFERENCE_LIST.md`.
*   **Validation**:
    *   **JSON Schema**: Validate against a strict schema (see `contracts/skill_package.schema.yaml`).
    *   **Asset Check**: Iterate through `IMAGE_REFERENCE_LIST.md` and verify file existence on the filesystem (fetched from HuggingFace).
    *   **Error Handling**: If an image is missing, log a warning, **increment `asset_error_count`**, mark the *step* as "ERROR", but **continue to the next step**. The *task* status is recorded as `partial_success` (if other steps pass) or `success` (if the missing asset is non-critical), depending on the implementation logic, but the `asset_error_count` is always incremented. This addresses the "Missing Image Assets" edge case and satisfies SC-005.
*   **Rigor**: This prevents "silent failures" where the agent crashes because an image is missing, ensuring that metrics reflect actual execution failures, not data corruption. The `asset_error_count` field in `metrics_summary.csv` directly measures SC-005.

### 3.3. Benchmark Execution & Timeout (FR-004, FR-005, SC-003)
*   **Method**: Execute a subset of tasks.
*   **Timeout**: Implement a hard timeout of 1800 seconds (30 minutes) per task using Python's `signal` module (Unix) or `threading` (cross-platform fallback).
*   **Memory Profiling**: Use `psutil` to record **Peak RSS** (Resident Set Size) memory usage for each task (SC-004). `tracemalloc` is insufficient as it only tracks Python heap, not native C++/PyTorch memory.
*   **Metrics**: Generate `metrics_summary.csv` with columns: `task_id`, `status` (success/fail/timeout/partial_success), `duration_seconds`, `peak_memory_mb`, `asset_error_count`, `error_message`.
*   **Rigor**: The timeout ensures the CI job does not hang. The metrics provide a quantitative measure of the pipeline's robustness (SC-001, SC-003, SC-004).
*   **Interpretation**: A "TIMEOUT" status indicates "Hardware Insufficiency" for the task on CPU, not necessarily a failure of the skill logic. This metric is for CI stability, not scientific validation of agent capability.

### 3.4. Structural Integrity vs. Performance (SC-002)
*   **Method**: Measure the percentage of tasks where the skill package was successfully parsed and the first step executed without parsing errors.
*   **Limitation**: Comparing this rate to the paper's GPU baseline is **scientifically invalid** due to hardware differences (CPU vs GPU) and sample size (N=5).
*   **Rigor**: The plan explicitly acknowledges this limitation. The success metric is "Structural Integrity" (can the code run?), not "Performance" (does it solve the task as well as the paper?). SC-002 is redefined as "Structural Execution Rate".

## 4. Compute Feasibility Analysis

*   **Hardware**: GitHub Actions Free Tier (multi-core CPU, high RAM).
*   **Memory**: The plan assumes the multimodal model weights (if loaded) are small enough to fit in available RAM. If the default model is too large (OOM), the plan mandates a fallback to a smaller, non-quantized CPU model or a mock agent.
*   **Time**: 5 tasks * 30 min max = 150 minutes (2.5 hours) + setup/teardown. This fits comfortably within the allocated time limit.
*   **Disk**: The `external/MMSkills` submodule, fetched dataset subset, and logs are expected to be < 14 GB.

## 5. Decision Rationale

*   **Why CPU-only?**: The CI environment lacks GPU drivers. Running on CPU ensures the validation is reproducible for all users and avoids CUDA dependency errors.
*   **Why 5 tasks?**: Running the full OSWorld benchmark is computationally expensive and time-consuming. A subset of 5 tasks is sufficient to validate the *execution flow*, *timeout logic*, and *metrics generation* without exceeding the CI time limit.
*   **Why strict timeout?**: To prevent a single hanging task from blocking the entire CI job, a hard timeout is essential for reliability.
*   **Why HuggingFace for data?**: Relying on a local submodule for binary assets is high-risk. The verified HuggingFace source ensures the data is complete and accessible.
*   **Why no Mock Data?**: Mock data cannot validate the "multimodal" claim. If the real data is missing, the study must fail, not simulate success.
*   **Why psutil?**: `tracemalloc` only tracks Python heap. `psutil` captures the total process RSS, which includes native model weights required for accurate SC-004 measurement.
*   **Why Schema Compatibility Check?**: To ensure the fetched dataset actually matches the expected skill structure, preventing runtime parsing errors and ensuring construct validity.