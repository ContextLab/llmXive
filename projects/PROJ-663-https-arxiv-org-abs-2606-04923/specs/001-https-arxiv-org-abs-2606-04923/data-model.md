# Data Model: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

## 1. Overview

This document defines the data structures used for the CHERRL reproduction pipeline. The data flow is unidirectional: **Input Data** (HealthBench) → **Processing** (Bias Injection, Training) → **Output Artifacts** (Logs, Reports).

## 2. Input Data Schemas

### 2.1 Training Dataset (Parquet)
*Source: `healthbench_train.parquet`*

| Field | Type | Description | Nullable |
| :--- | :--- | :--- | :--- |
| `id` | string | Unique identifier for the sample. | No |
| `prompt` | string | The input prompt given to the agent. | No |
| `completion` | string | The ground-truth or expected completion. | Yes |
| `metadata` | json | Additional context (e.g., difficulty, category). | Yes |

### 2.2 Bias Configuration (YAML)
*Source: `configs/bias_config.yaml` (SSoT)*

| Field | Type | Description |
| :--- | :--- | :--- |
| `bias_type` | string | One of: `self-praise`, `lexical`, `tone`. |
| `trigger_tokens` | list[string] | List of tokens or phrases that trigger the bias. |
| `reward_boost` | float | The magnitude of the reward increase when trigger is detected. |
| `description` | string | Human-readable description of the bias. |

## 3. Output Data Schemas

### 3.1 Training Log (JSONL)
*Source: `outputs/logs/run_<bias_type>.jsonl`*

Each line represents a single training step.

| Field | Type | Description |
| :--- | :--- | :--- |
| `step` | int | The training step index. |
| `timestamp` | string | ISO 8601 timestamp. |
| `prompt` | string | The prompt sent to the agent. |
| `completion` | string | The agent's generated response. |
| `judge_score` | float | The raw score assigned by the Judge (biased). |
| `ground_truth_quality` | float | The score based on independent ground-truth quality (unbiased). |
| `bias_triggered` | bool | Whether the bias trigger was detected in the completion. |
| `trigger_tokens` | list[string] | The specific tokens that triggered the bias (if any). |

### 3.2 Detection Report (CSV)
*Source: `outputs/reports/threshold_grid.csv`*

| Field | Type | Description |
| :--- | :--- | :--- |
| `threshold` | float | The detection threshold used. |
| `detected_onset_step` | int | The step identified as the start of hacking. |
| `true_positives` | int | Number of correct detections. |
| `false_positives` | int | Number of incorrect detections. |
| `true_negative_rate` | float | Proportion of non-hacking steps correctly identified. |
| `false_negative_rate` | float | Proportion of hacking steps missed. |

## 4. Data Flow Diagram

```mermaid
graph TD
    A[Input: HealthBench Dataset (Parquet)] --> B(Sanity Check & Load)
    B --> C{Bias Config (SSoT)}
    C -->|Self-Praise| D[Training Loop: Bias Run]
    C -->|Lexical| D
    C -->|Tone| D
    C -->|None| E[Training Loop: Baseline]
    D --> F[Output: Training Logs (JSONL)]
    E --> F
    F --> G[RHDA Detection Agent]
    G --> H[Output: Sensitivity Report (CSV)]
```

## 5. Constraints & Validations

-   **Character Limits**: Prompts and completions must be truncated to the model's maximum context window (e.g., 4096 tokens) before processing.
-   **Numerical Stability**: Reward scores are normalized to [0, 1] or [-1, 1] range to prevent overflow in log aggregation.
-   **Missing Data**: If `ground_truth_quality` is missing, the `reward_divergence` metric is calculated relative to the baseline mean, not an absolute ground truth.