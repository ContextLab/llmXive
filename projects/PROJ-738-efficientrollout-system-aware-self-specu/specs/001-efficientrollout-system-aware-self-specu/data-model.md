# Data Model: EfficientRollout

## 1. Overview

This document defines the data structures for the `EfficientRollout` validation pipeline. The system processes a subset of prompts, generates rollout traces via two methods (Baseline AR and EfficientRollout SD), and outputs structured JSON logs for analysis.

## 2. Entities

### 2.1 Prompt
A single input text for the model.
-   **Source**: Local JSONL file (`prompts.jsonl`) - **Single Source of Truth**.
-   **Schema**: `Prompt`

### 2.2 Rollout Trace
The sequence of tokens generated, annotated with acceptance/rejection flags and timing.
-   **Source**: Output of `sd_toggle` or `baseline` module.
-   **Schema**: `RolloutTrace`

### 2.3 Run Summary
Aggregated metrics for a single run (Baseline or SD).
-   **Source**: Aggregation of `RolloutTrace` objects.
-   **Schema**: `RunSummary`

## 3. Data Schemas

### 3.1 Prompt
```yaml
id: str          # Unique identifier (e.g., "prompt_001")
text: str        # The input prompt string
```

### 3.2 RolloutTrace
```yaml
run_id: str                  # Unique run identifier
prompt_id: str               # Reference to Prompt
method: str                  # "baseline" or "speculative"
tokens: list[str]            # Generated token sequence
acceptance_flags: list[bool] # True if token accepted, False if rejected (only for speculative)
latency_per_token: list[float] # Time in seconds for each token generation
total_latency: float         # Total time in seconds
memory_peak_mb: float        # Peak RAM usage during generation
toggle_decision: str         # "enable" or "disable" (only for speculative)
trial_index: int             # 0, 1, or 2 (for variance estimation)
```

### 3.3 RunSummary
```yaml
run_id: str
method: str
prompt_count: int
total_tokens: int
avg_latency_per_token: float
total_latency: float
acceptance_rate: float       # For speculative runs (accepted / total drafted)
speedup_vs_baseline: float   # Calculated ratio (only for SD runs)
cv_latency: float            # Coefficient of variation of latency across trials
toggle_logic_validated: bool # True if synthetic regime test passed
```

## 4. Data Flow

1.  **Input**: `prompts.jsonl` (10 lines). **Fail if missing**.
2.  **Process**:
    -   Load Model & Quantize (CPU).
    -   Run Baseline AR (3 trials) -> Generate `RolloutTrace` (Baseline).
    -   Run Speculative SD (3 trials) -> Generate `RolloutTrace` (Speculative).
    -   Run Synthetic Regime Test (1 trial) -> Validate Toggle Logic.
3.  **Output**:
    -   `logs/run_<timestamp>_baseline.json`
    -   `logs/run_<timestamp>_speculative.json`
    -   `results/summary_<timestamp>.json`

## 5. Storage Constraints

-   **Input Size**: < 100KB (10 prompts).
-   **Output Size**: < 1MB (Logs + Traces).
-   **Model Artifacts**: < 6GB (Quantized 8B model).
-   **Total Disk Usage**: < 8GB (Fits within 14GB limit).