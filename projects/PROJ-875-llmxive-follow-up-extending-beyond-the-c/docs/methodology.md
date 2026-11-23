# Methodology: llmXive Follow-Up Study

## Overview

This document details the methodology for the llmXive follow-up study, "Extending Beyond the Current Observation: Evaluating Multimodal Large Language Models." It describes the data generation pipeline, the agent architectures, the scoring mechanisms, and the statistical analysis plan.

## 1. Data Generation (RNG-Bench)

The study utilizes a procedurally generated environment (RNG-Bench) to create reproducible, deterministic test cases.

### 1.1. Seed Configuration
- **Source**: `config/seeds.yaml`
- **Content**: A pinned list of integer seeds ensuring exact reproducibility of grid states and event logs.
- **Usage**: Seeds are passed to `code/renderer.py` to generate both ASCII grids and visual frames.

### 1.2. Renderer Pipeline
- **Implementation**: `code/renderer.py`
- **Outputs**:
 1. **ASCII Grids**: Text-based representations of the environment state (`.ascii` files).
 2. **Event Logs**: JSON logs detailing every time step and state transition (`.json` files).
 3. **Visual Frames**: Raw image files (`.png`) representing the visual state at each step.
- **Validation**: The renderer includes strict bounds checking. Any out-of-bounds state triggers a standardized `ERROR: STATE_CORRUPT` block.
- **Fidelity Check**: `utils/renderer_validator.py` is executed post-generation to verify that the ASCII grid representation matches the visual frame pixel-for-pixel (Levenshtein distance = 0), ensuring data hygiene.

## 2. Agent Architectures

The study compares two distinct agent modalities operating on the same underlying environment seeds.

### 2.1. Text-Only Agent (Baseline)
- **Input**: ASCII grid strings and JSON event logs.
- **Model**: Quantized text-only LLM (≤3B parameters), loaded via CPU-optimized engine.
- **Processing**:
 - Receives the ASCII representation of the current state.
 - Maintains a mental map (context window) with a sliding window strategy (keeping the last N=50 events).
 - Outputs a structured JSON action and updated mental map.
- **Resource Constraints**: Hard step limits and memory profiling (≤7GB RAM) are enforced. Runs exceeding these limits are discarded and logged.

### 2.2. Multimodal Baseline Agent (Visual Input)
- **Input**: Raw Visual Frames (PNG images).
- **Model**: Vision-capable Multimodal LLM (e.g., Qwen-VL-Chat-Int4).
- **Processing**:
 - Receives raw image frames directly, bypassing the ASCII abstraction.
 - Processes visual tokens to infer state and history.
 - Outputs structured JSON actions and mental maps via `code/baseline_adapter.py`.
- **Modality Isolation**: This agent operates *only* on visual inputs to isolate the impact of modality on memory retention.

## 3. Metric Definition: Structured JSON + Semantic Similarity

The primary metric, "Memory Gap," has been redefined via Plan Override (refer to `docs/kickbacks/001-metric-baseline-override.md`) to move beyond simple string matching.

### 3.1. Calculation Formula
The Memory Gap Score is calculated as the sum of two components:

$$ \text{Score} = (1 - \text{SemanticSimilarity}) + (1.0 \times \text{MissingCriticalItems}) $$

Where:
1. **Semantic Similarity**: Calculated using `sentence-transformers/all-MiniLM-L6-v2`. The agent's recalled state (mental map) is compared against the masked ground truth.
 - If `semantic_similarity < 0.5`, it is treated as 0.0 for the penalty calculation to enforce a hard threshold on recall quality.
2. **Missing Critical Items**: A count of critical items (e.g., keys, doors) present in the `masked_ground_truth` but missing from the `agent_mental_map`. Each missing item incurs a penalty of 1.0.

### 3.2. Ground Truth Masking
- **Logic**: Implemented in `code/scorer.py` and `utils/hasher.py`.
- **Application**: Both the Text Agent and the Visual Baseline are scored against the *same* masked ground truth state derived from the RNG-Bench seeds. This ensures a fair comparison of modality impact rather than task difficulty differences.

## 4. Baseline: Visual Input Strategy

To ensure a valid comparison of modality impact, the study employs a strict Baseline Visual Input Strategy:

- **Re-execution**: The baseline MLLM is re-run on the exact same Visual inputs (raw frames) generated from the same RNG-Bench seeds used for the text-only agent.
- **Consistency**: The "Memory Gap" metric is calculated on the same masked ground truth state for both agents.
- **Rationale**: This strategy isolates the variable of "modality of input" (Text vs. Visual) while controlling for environmental complexity and ground truth availability.

## 5. Statistical Analysis

### 5.1. Aggregation
- **Tool**: `code/stats.py`
- **Process**:
 1. Load all `agent_run_*.json` and `baseline_run_*.json` from `data/processed/`.
 2. Extract `memory_gap_score` for each run.
 3. Compute mean, standard deviation, and 95% confidence intervals for both groups.

### 5.2. Hypothesis Testing
- **Test**: One-tailed Mann-Whitney U test.
- **Null Hypothesis ($H_0$)**: The distribution of Memory Gap scores for the Text Agent is not stochastically greater than the Visual Baseline.
- **Alternative Hypothesis ($H_1$)**: The Text Agent has a significantly higher Memory Gap score (worse retention) than the Visual Baseline.
- **Significance Level**: $\alpha = 0.05$.
- **Output**: `results/statistical_summary.json` containing $p$-values and the final conclusion.

## 6. Data Hygiene and Reproducibility

- **Checksums**: `utils/checksum.py` generates SHA-256 checksums for all files in `data/processed/`.
- **Versioning**: `utils/hasher.py` creates version hashes for artifacts to track provenance.
- **Validation**: All data pipelines are validated against schema contracts defined in `specs/contracts/`.
- **Execution**: Final results are generated by running `code/main.py` with the `--mode pilot` or `--mode full` flags.