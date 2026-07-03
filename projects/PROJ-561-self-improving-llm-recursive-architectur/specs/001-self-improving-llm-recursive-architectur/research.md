# Research: Self-improving LLM: recursive architecture refinement and re‑training

## Summary

This research plan investigates the feasibility of recursive self-improvement in LLMs under strict computational constraints (CPU-only, 7GB RAM). The core hypothesis is that a GPT 124M model can propose valid architectural modifications that, after 1 epoch of re-training on a language modeling task, yield statistically significant improvements in reasoning (GSM8K, ARC) and calibration (ECE) without exceeding a [deferred] parameter budget.

**Critical Scope Adjustment**: Due to the strict 6-hour time limit and 7GB RAM constraint of the GitHub Actions free-tier runner, the **primary deliverable is a Single Cycle (US-1)**. The 3-cycle trajectory (US-2) is re-classified as a "Scaling Study" that will only be attempted if the single cycle completes successfully within 1.5 hours.

**Data Integrity Policy**: The pipeline enforces a strict **Fail-Fast** policy for all datasets (OpenWebText, GSM8K, ARC-Challenge, Wikitext-2). If these datasets cannot be loaded from their standard HuggingFace sources, the pipeline **terminates immediately** with a specific error code. **Synthetic data is NOT permitted for any part of the experiment**, including training or evaluation. Training on synthetic data renders the "recursive improvement" hypothesis untestable, and evaluation on synthetic data yields meaningless metrics. The experiment is designed to fail if verified data sources are unavailable.

## Dataset Strategy

The project requires four distinct datasets: **OpenWebText** (training), **GSM8K** (reasoning benchmark), **ARC-Challenge** (reasoning benchmark), and **Wikitext-2** (calibration benchmark).

**Constraint**: The plan relies on standard HuggingFace loaders for these datasets. If these loaders fail, the pipeline terminates immediately. No synthetic data is permitted as a fallback.

**Strategy**:
1.  **Primary Attempt**: The implementation will attempt to load these datasets using the standard `datasets` library (e.g., `load_dataset("gsm8k", "main")`, `load_dataset("HuggingFaceH4/openwebtext", ...)`). These loaders typically point to public HuggingFace repositories.
2.  **Fail-Fast (All Datasets)**: If **any** dataset (OpenWebText, GSM8K, ARC-Challenge, or Wikitext-2) fails to load:
    *   Log a critical error: "Dataset [Name] unavailable via standard loader. Terminating pipeline."
    *   **Terminate the pipeline immediately**.
    *   Do not proceed to training or evaluation.
    *   Record the status as "failed" for the dataset.
    *   **No metrics** are computed or recorded for this cycle.

**Dataset Table**:

| Dataset | Intended Use | Source Strategy | Fallback Policy |
| :--- | :--- | :--- | :--- |
| **OpenWebText** | Training (1 epoch) | `datasets.load_dataset("HuggingFaceH4/openwebtext")` (Standard HF loader) | **FORBIDDEN**: Fail-Fast (Terminate) |
| **GSM8K** | Reasoning Benchmark | `datasets.load_dataset("gsm8k", "main")` | **FORBIDDEN**: Fail-Fast (Terminate) |
| **ARC-Challenge** | Reasoning Benchmark | `datasets.load_dataset("allenai/ai2_arc", "ARC-Challenge")` | **FORBIDDEN**: Fail-Fast (Terminate) |
| **Wikitext-2** | Calibration (ECE) | `datasets.load_dataset("wikitext", "wikitext-2-raw-v1")` | **FORBIDDEN**: Fail-Fast (Terminate) |

*Note: No URLs are cited in this document as they are not present in the verified block. The implementation relies on standard library loaders. If these loaders fail, the experiment cannot proceed.*

## Methodological Rigor

### Statistical Approach
*   **Paired Bootstrap**: For each cycle, we will perform paired bootstrap testing (1000 resamples) comparing the baseline (pre-modification) and post-modification metrics (GSM8K accuracy, ARC accuracy, ECE).
    *   **Hypothesis**: $H_0$: $\mu_{post} - \mu_{pre} \le 0$ (No improvement).
    *   **Significance**: $\alpha = 0.05$. Strictly $p < 0.05$ required for significance (per Edge Case spec).
    *   **Correction**: Since we are testing 3 benchmarks per cycle, we will apply a Bonferroni correction ($\alpha_{adj} = 0.05 / 3 \approx 0.0167$) to the p-values to control family-wise error rate, or report both raw and corrected p-values.
    *   **Constraint**: If any dataset fails to load, **no statistical testing is performed**, and the cycle is marked as failed.
*   **Trajectory Modeling**: We will fit an exponential decay model $y = a \cdot e^{-bx} + c$ to the performance trajectory (accuracy vs. cycle number) using non-linear least squares (`scipy.optimize.curve_fit`).
    *   **Plateau Definition**: Cycle $n$ where $(y_n - y_{n-1}) / y_{n-1} \le 0.01$.
    *   **Degradation Definition**: Cycle $n$ where $(y_n - y_{n-1}) / y_{n-1} \le -0.01$.
    *   **Constraint**: This analysis is only performed if at least 2 cycles complete successfully with valid benchmark data.

### Causal & Validity Considerations
*   **Observational Nature**: This is an observational study of the model's self-modification process. We cannot claim "causal" improvement in the general sense, only associational improvement *within the specific experimental setup*.
*   **Measurement Validity**: GSM8K and ARC-Challenge are standard benchmarks for reasoning. ECE on Wikitext-2 is a standard calibration metric.
*   **Collinearity**: The "modification" is proposed by the model itself. If the model proposes a change that simply adds parameters without changing logic, any performance gain might be due to capacity, not "intelligence." We will track parameter count vs. performance to distinguish these.
*   **Data Source Independence**: To address von Neumann's concern (Constitution Principle VII), the evaluation set (GSM8K/ARC) is **never** used to generate the modification prompt. The prompt is generated **solely** from the training loss on OpenWebText and the model's internal state (weights). The evaluation results are strictly excluded from the prompt generation loop.

## Compute Feasibility & Risk Mitigation

**Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 14GB Disk).

**Risks**:
1.  **RAM Overflow**: Loading GPT-2 124M + training overhead might exceed 7GB.
    *   *Mitigation*: Use `gradient_checkpointing` in `transformers`. Use `batch_size=2` (reducing to 1 if >6.5GB). Implement a "Memory Watchdog" that monitors RAM usage. If usage > 6.5GB, reduce batch size to 1. If usage > 7GB, kill the process to prevent system crash.
    *   *Proactive Measures*: Unload model from memory before training, use `torch.no_grad()` for evaluation, and enable CPU offloading for activations.
2.  **Runtime > 6 Hours**: Training 3 cycles + evaluation might exceed time limits.
    *   *Mitigation*: Limit OpenWebText subset to [deferred] samples (e.g., tens of thousands). Limit evaluation to a subset of the benchmark (e.g., first 100 samples of GSM8K) if necessary, though this reduces statistical power. **Primary Goal**: Complete Single Cycle within 1.5 hours. If not, terminate.
3.  **Model Proposal Failure**: The model might propose an invalid architecture (e.g., negative layers).
    *   *Mitigation*: Implement a validation step in `model.py` that parses the LLM's JSON output. If invalid, re-prompt with a stricter constraint. Retry up to 2 times (per Edge Case).
4.  **Dataset Unavailability**: Benchmarks fail to load.
    *   *Mitigation*: Fail-Fast. Do not proceed with synthetic data for any part of the experiment.

**Decision Rationale**:
*   **CPU Only**: No GPU is available. We use `torch` CPU builds.
*   **Small Model**: GPT-2 124M is chosen because it is the smallest standard GPT-2 variant, making it the only viable candidate for CPU training within 7GB RAM.
*   **1 Epoch**: Training for 1 epoch is a trade-off to stay within the 6-hour window while demonstrating the mechanism.
*   **No Synthetic Data**: Synthetic data cannot measure reasoning or language modeling. Therefore, if datasets are unavailable, the experiment cannot be validated, and the pipeline must terminate.

## Timeline (Estimated)

**Primary Goal**: Single Cycle (US-1)
1.  **Cycle 1**: Download -> Prompt -> Modify -> Train (1h) -> Evaluate (30m) -> Stats (10m) = ~1.5h
2.  **Buffer**: 30m for retries/backoff.
**Total**: ~1.8h. *Risk*: Tight margin. Mitigation: Aggressive subset sizing.

**Scaling Study (Conditional)**:
If Cycle 1 completes within 1.5 hours, proceed to Cycle 2 and 3.
1.  **Cycle 2**: ~1.5h
2.  **Cycle 3**: ~1.5h
3.  **Analysis**: Trajectory fitting, trade-off analysis = 30m
**Total**: ~5.3h. *Risk*: High probability of timeout on free-tier. If timeout occurs, log "Incomplete - Timeout" and report available data.