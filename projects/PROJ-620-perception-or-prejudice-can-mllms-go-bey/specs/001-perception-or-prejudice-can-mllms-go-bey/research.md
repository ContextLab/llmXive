# Research: Reproduction of MM-OCEAN Benchmark

## Problem Statement

The MM-OCEAN benchmark evaluates Multimodal Large Language Models (MLLMs) on their ability to infer personality traits from video, specifically distinguishing between "Perception" (grounded analysis) and "Prejudice" (stereotyping). The goal is to **reproduce the paper's key findings**—specifically the "Prejudice Gap" and "Holistic-Grounding Rate"—using the vendored codebase on a constrained CPU-only environment.

**Scope Clarification**: This study is a **code reproduction** and **validity check** of the original paper's methodology. It does not claim to independently validate the scientific truth of the "Prejudice Gap" phenomenon without an external ground truth (e.g., human annotation). The primary scientific claim is: "The MM-OCEAN codebase, when run on the specified hardware, reproduces the numerical results reported in the paper."

## Dataset Strategy

The primary dataset is the **MM-OCEAN** benchmark.

| Dataset Name | Source URL | Usage | Notes |
| :--- | :--- | :--- | :--- |
| MM-OCEAN (Metadata) | https://huggingface.co/datasets/anonymous-mm-ocean/MM-OCEAN/resolve/main/croissant.json | Schema & Metadata Verification | Contains the definition of the benchmark structure. |
| MM-OCEAN (Test Set) | **Local**: `data/test` | Inference Input | The actual video files and JSON annotations are vendored in the repository. **NO external download** is required during CI, satisfying the "self-contained" assumption in the spec. |

**Variable Fit Confirmation**:
- **Required**: Video content, Big Five scores (ground truth), behavioral cues, model ratings, reasoning traces.
- **Availability**: The `data/test` directory contains paired video files and JSON annotations. The vendored `MM-OCEAN` codebase is designed to ingest this structure.
- **Constraint**: The dataset size (number of videos) is [deferred]. The plan **commits to processing the entire `data/test` set**. If the full set exceeds the 6-hour CI limit, a **stratified random sample** (stratified by video length and complexity) will be drawn *before* inference begins, and the sampling fraction will be explicitly documented. **Arbitrary limits (e.g., `--limit 10`) are strictly for debugging and invalid for final metric validation.**

## Technical Approach

### 1. Environment & Model Loading (FR-003)
- **Constraint**: No GPU/CUDA.
- **Method**:
  - Force `torch` to use CPU: `torch.set_num_threads(2)` and `torch.backends.openmp.set_num_threads(2)`.
  - Disable CUDA in `transformers`: `device_map="cpu"`, `torch_dtype=torch.float32`.
  - **Critical**: Do NOT use `load_in_8bit` or `bitsandbytes` as they require CUDA.
  - If the model architecture is incompatible with CPU (rare), log a `WARNING` and skip the model (Edge Case: Model Loading Failures).

### 2. Inference Pipeline (FR-001, FR-005)
- **Streaming**: Video frames will be extracted on-the-fly using `opencv-python` or `decord` with a buffer limit to prevent RAM exhaustion.
- **Timeout**: A `signal.timeout` or `threading.Timer` wrapper will enforce a 600-second limit per video sample. If exceeded, the sample is marked as `TIMEOUT` and skipped.
- **Batching**: Process samples sequentially to manage RAM usage within system memory constraints.

### 3. Metric Calculation (FR-002)
The four failure-mode metrics are computed as follows:
- **Prejudice Rate (PR)**: % of samples where the model's reasoning relies on stereotypes rather than visual evidence.
- **Confabulation Rate (CR)**: % of samples where the model invents details not present in the video.
- **Integration-failure Rate (IR)**: % of samples where the model fails to combine visual and textual cues correctly.
- **Holistic-grounding Rate (HR)**: % of samples where the model's reasoning is fully grounded in the video content.

*Note: The exact logic for classifying these modes is embedded in the vendored `MM-OCEAN` code. The reproduction plan assumes this logic is correct for the purpose of code reproduction, but includes a sanity check (see Validation Strategy).*

### 4. Reporting (FR-006)
- **Output**: A `summary_report.md` and `failure_mode_distribution.png`.
- **Content**:
  - Table of PR, CR, IR, HR for each model.
  - Bar chart comparing PR across models.
  - Top 3 failure modes by frequency.

### 5. Validation Strategy (Addressing Circular Logic)
To address the risk that the "Prejudice" label is defined solely by the code being tested:
1. **Heuristic Sanity Check**: A secondary, independent heuristic will be applied to the reasoning traces. This heuristic uses keyword matching (e.g., presence of generic stereotype terms like "typically", "usually", "men are", "women are") to flag potential stereotyping. This provides a `validation_source` of "heuristic" for comparison.
2. **Transparency**: The `validation_source` field in the output schema will explicitly state whether the flag was derived from "vendored_code", "heuristic", or "human_review".
3. **Scope Limitation**: The study explicitly states that it validates the *code's reproduction of the paper's numbers*, not the *scientific truth* of the paper's claims without independent ground truth.

## Statistical Rigor & Limitations

- **Sample Size**: The number of test samples is [deferred]. If the sample size is small (<30), the confidence intervals for the metrics will be wide.
- **Power**: No power analysis is possible without knowing the exact effect size of the "Prejudice Gap" in the original paper's full dataset. We will report the raw rates and compare them to the paper's reported values using **Equivalence Testing (TOST)** *only if* the sample size is sufficient to achieve a 90% CI width < 0.10. If the sample is too small, TOST is skipped, and the point-estimate check (±5%) stands alone with a limitation note.
- **Equivalence Testing**: To validate reproduction, we will perform a Two One-Sided T-test (TOST) with an equivalence margin (delta) of a predefined small magnitude. If the % CI of the difference between reproduced and reported metrics falls entirely within [-0.05, 0.05], the reproduction is considered statistically equivalent. This is stricter than the spec's ±5% tolerance and provides a confidence interval.
- **Causal Claims**: This is a reproduction of an observational benchmark. No causal claims are made; the study is purely descriptive of model behavior.
- **Multiple Comparisons**: If comparing multiple models, we will report the metrics for each without aggressive correction, as the primary goal is reproduction, not hypothesis testing of a new effect.
- **Dropout Analysis**: If the dropout rate (samples skipped due to timeout/error) exceeds 5%, a sensitivity analysis will be performed to check if dropped samples differ significantly from processed samples (e.g., by video length). If bias is detected, the metrics will be reported with a "bias-adjusted" estimate or the study will be marked as "inconclusive due to bias".

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-only Execution** | Required by the GitHub Actions free-tier (2 CPU, 7 GB RAM). GPU methods are infeasible. |
| **Streaming Frames** | Prevents disk/RAM exhaustion when processing video files. |
| **Timeout per Sample** | Ensures the 6-hour CI job completes even if a single video causes a hang. |
| **Vendored Code** | Preserves the original logic of `MM-OCEAN` to ensure a fair reproduction. |
| **TOST Equivalence Test** | Provides a statistically valid method to compare reproduced vs. reported metrics, avoiding arbitrary tolerance thresholds (if sample size permits). |
| **Dropout Sensitivity** | Ensures that missing data does not bias the final metrics. |
| **Heuristic Sanity Check** | Provides a secondary, independent check against circular validation of "Prejudice" labels. |