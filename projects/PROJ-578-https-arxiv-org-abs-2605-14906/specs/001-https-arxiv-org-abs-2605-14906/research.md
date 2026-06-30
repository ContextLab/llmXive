# Research: Reproduce & Validate MemLens Benchmark

## Dataset Strategy

The MemLens benchmark relies on a specific dataset of multimodal questions and conversation histories. The research plan confirms that the dataset is not a generic external source but is **vendored** as part of the `MEMLENS` submodule.

**Dataset Source**: `MEMLENS` submodule (Git)
**Access Method**: The `eval.py` script expects the dataset to be present in the `data/` directory of the vendored submodule.
**Verification**: The spec assumes the submodule is cloned correctly. The plan includes a pre-flight check to verify the presence of expected JSONL files (e.g., `questions.jsonl`, `context.jsonl`) before execution.

**Note on External Datasets**: The "Verified datasets" list provided in the input context contains unrelated datasets (e.g., `ideogram-v4`, `metatree_cpu`, `lex-fridman`). **None of these are the MemLens benchmark dataset.** The MemLens benchmark is a self-contained codebase with its own data. Therefore, no external URL from the provided list will be cited or used for the primary evaluation. The plan strictly uses the vendored data.

## Methodological Rigor & Statistical Considerations

### Visual Evidence Dependency (US-2)
The plan validates the claim that "solving these tasks genuinely requires visual evidence" by comparing two conditions:
1.  **Full Multimodal**: Model receives text + image.
2.  **Ablated**: Model receives text only (image replaced with null/empty token).

**Statistical Approach**:
-   **Metric**: Accuracy (percentage of correct answers).
-   **Hypothesis**: Accuracy in the Ablated condition will be significantly lower than the Full Multimodal condition for image-dependent questions.
-   **Effect Size**: The paper claims accuracy drops to <2% in the ablated condition. This is the *expected effect size* to be verified, not the significance threshold.
-   **Statistical Test**: McNemar's test for paired proportions will be used, as the same questions are evaluated in both conditions. The significance level will be set at p < 0.05.
-   **Correction**: Since multiple question subsets are tested, a Bonferroni correction or False Discovery Rate (FDR) control will be applied if multiple hypothesis tests are run across the five memory abilities.
-   **Power**: The sample size is determined by the available benchmark questions. If the subset is small, the plan will explicitly acknowledge the power limitation in the final report.

**Validation of Ground Truth**:
The "LLM Judge" (`llm_judge.py`) is used only for text-only answers in the ablation condition. For the full multimodal condition and for determining ground truth, the plan relies on human-annotated ground truth from the dataset. This avoids the circular validation of using a text-only judge to verify image-dependent answers.

### Scaling & Memory Trends (US-3)
The plan examines performance degradation across varying context lengths.
-   **Method**: Descriptive analysis of Accuracy vs. Context Length (token count).
-   **Assumption**: The relationship is expected to be negative (performance drops as context grows).
-   **Causal Claim**: This analysis is **purely descriptive and associational**. Context length is a fixed configuration parameter, not a random variable. The regression on discrete points (varying scales) does not support causal inference regarding model architecture or capacity. The plan will explicitly state this limitation.
-   **API Context Integrity**: If API-based evaluation is used, a pre-flight check will verify that the API provider actually processes the full context window. The plan will log the actual token count received by the model and compare it to the input token count. If the API truncates the context, the run is flagged as 'truncated' and excluded from the scaling analysis to avoid measuring API truncation policies instead of model memory capacity.

### Measurement Validity
-   **Instruments**: The "LLM Judge" (`llm_judge.py`) is used for scoring. The plan assumes this instrument is validated in the paper for text-only answers.
-   **Collinearity**: Context length and model capacity are distinct variables. However, if "memory ability" categories are derived from the same underlying data structure, their independence will be noted.

## Compute Feasibility Analysis

The target environment is a GitHub Actions free-tier runner with limited CPU and RAM resources and no GPU.

1.  **Model Constraints**:
    -   **Local CPU Inference**: Running LLaVA-7B on 7GB RAM is not possible, even with 4-bit quantization, due to the overhead of CPU inference and the 256K context window. The plan restricts local CPU inference to models with <2B parameters (e.g., TinyLLaVA) or uses 4-bit quantization with a memory-mapped loading strategy and aggressive chunking.
    -   **API-based Evaluation**: For larger models (7B+), the plan prioritizes **API-based evaluation** (e.g., GPT-4, Claude) to ensure feasibility on CPU-only CI. However, the plan explicitly notes that results from API models may be confounded by provider-specific infrastructure (e.g., internal truncation, compression). The primary goal is to reproduce the *original paper's results* using the specific models described. API calls are a fallback for models not available locally.
2.  **Memory Management**:
    -   **Chunking**: For 256K context windows, the plan mandates a "chunked processing" mode where the context is split into manageable segments if the full window exceeds RAM.
    -   **Sampling**: The plan will use a **sampled subset** of the benchmark (e.g., 10-50 questions per context length) for the initial CI run to ensure it completes within 60 minutes and fits in 7GB RAM.
3.  **Runtime**: A fixed time limit is sufficient for a sampled run. Full runs on large models via API are time-constrained by API rate limits, not local compute.

## Decision Log

-   **Decision**: Prioritize local CPU inference for small models (<2B) and API calls for larger models (7B+).
    -   **Rationale**: Local CPU inference of 7B+ models is physically impossible on the target hardware (7GB RAM). API calls are the only feasible way to test the "benchmarking" aspect on large models, with the caveat of potential confounds.
-   **Decision**: Sample the dataset for CI runs.
    -   **Rationale**: Full dataset evaluation exceeds the specified time and memory constraints. The plan defines a "sampled run" as the standard CI test, with a note that full runs require a dedicated runner.
-   **Decision**: Do not use external datasets from the "Verified datasets" list.
    -   **Rationale**: The MemLens benchmark is self-contained. Using unrelated datasets would violate the spec's requirement to reproduce the specific MemLens paper.
-   **Decision**: Frame scaling analysis as descriptive/associational.
    -   **Rationale**: Context length is a fixed configuration, not a random variable. Causal claims are not supported by the design.
