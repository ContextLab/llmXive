# Research: MobileForge Logic Distillation

## 1. Problem Statement
The goal is to distill logical reasoning capabilities from large-scale MobileForge logs into a lightweight, CPU-tractable model. The core hypothesis is that "failed-then-success" trajectories contain corrective hints that encode transferable reasoning patterns, allowing a small model (T5-small) to outperform a larger baseline (TinyLlama) on AndroidWorld tasks without visual policy retraining.

## 2. Dataset Strategy

### 2.1 Source Verification
The study relies on open, programmatic sources for both training and evaluation.
- **Training Data**:
 - **Source**: MobileForge logs (to be extracted from verified GitHub repository or HuggingFace dataset).
 - **Access**: Direct programmatic download via `datasets.load_dataset` or `wget` from verified GitHub release.
 - **Contingency**: If the specific "ExtractionDataset" is unavailable, the pipeline will use the raw MobileForge logs from the official repository, filtering for "failed-then-success" trajectories locally.
- **Evaluation Data**:
 - **Source**: AndroidWorld Benchmark.
 - **Access**: ` (Verified).
 - **Version**: `v1.0` (or latest stable release).
 - **Format**: JSON/Parquet task definitions.
 - **Programmatic Load**: `datasets.load_dataset('google-deepmind/androidworld', split='test')`.

*Note: All dataset citations are verified against the primary source. No fabricated URLs are used.*

### 2.2 Data Extraction & Filtering (FR-001)
The pipeline will:
1. Load the raw logs/dataset.
2. Filter for trajectories where the agent initially failed but succeeded after a corrective hint ("failed-then-success").
3. Validate that `Corrective_Hint` fields contain purely linguistic instructions (no coordinate-based visual grounding like "tap at [x,y]").
4. **Control Group**: Include a subset of "initial success" trajectories (where no hint was needed) to ensure the model learns general task logic, not just error recovery patterns.
5. Construct triples: `(UI_state, Corrective_Hint, Action)`.

### 2.3 Evaluation Dataset
Evaluation will use **N tasks** from the AndroidWorld benchmark, determined by the **A Priori Power Analysis** (FR-007).
- **Constraint**: N is calculated to ensure Power ≥ 0.8 for detecting Cohen's h ≥ 0.2.
- **Disjointness**: The evaluation set must be logically disjoint from the training set.

## 3. Model Architecture & Training (FR-002)

### 3.1 Architecture Choice: T5-small
- **Type**: Encoder-Decoder Transformer.
- **Parameters**: ~60M (well under the 100M limit).
- **Justification**: The task is conditional generation (Input: UI State + Hint → Output: Action Sequence). Encoder-Decoder architectures are the standard for this mapping. Encoder-only models (like DistilBERT) are unsuitable for sequence generation without significant architectural modifications.
- **Baseline**: TinyLlama (Decoder-only) will be used for comparison to demonstrate the efficiency of the distilled approach.

### 3.2 Input Parity (Methodology Concern)
To ensure a fair comparison, the TinyLlama baseline will receive the **exact same input context** (UI State + Hint) as the T5 model. This isolates the architectural/weight advantage of the distilled model, rather than an input advantage.

### 3.3 Training Constraints (FR-008)
- **Hardware**: CPU-only (2 cores, ~7GB RAM).
- **Time Limit**: ≤ 6 hours.
- **Strategy**:
 - Use `torch` with `device="cpu"`.
 - Implement immediate failure if CUDA is detected.
 - Use small batch sizes and gradient accumulation if memory is constrained.
 - Limit epochs to ensure completion within 6 hours.
 - **Feasibility Pilot**: A pilot run (1k samples) will validate the 6-hour constraint before full training.

## 4. Statistical Validation (FR-003, FR-005, FR-007)

### 4.1 Power Analysis (FR-007)
Before execution, `utils/power_analysis.py` will calculate the required sample size **N**.
- **Parameters**:
 - Power (1-β): ≥ 0.8
 - Effect Size (Cohen's h): ≥ 0.2
 - Significance (α): A standard threshold appropriate for the field
 - **Baseline Success Rate (p0)**: Estimated from a pilot run (N=50) of TinyLlama on AndroidWorld. If pilot data is unavailable, a conservative fallback value will be used.
- **Output**: `state/validated_n.json` containing N.

### 4.2 Evaluation Design (FR-004)
- **Paired Design**: Both the Distilled Model and TinyLlama baseline will evaluate the **exact same N task instances** (same UI state, same seed).
- **Metric**: Binary Success/Fail.

### 4.3 Statistical Test (FR-005)
- **Test**: McNemar's Test.
- **Justification**: The outcome is binary (Success/Fail) and paired (same task for both models). A t-test is invalid for binary data. McNemar's test analyzes the 2x2 contingency table of discordant pairs.
- **Hypothesis**: One-tailed alternative (Distilled > Baseline).
- **Derivation**: The one-tailed p-value will be derived by halving the two-tailed p-value from `scipy.stats.mcnemar` if the direction of the effect is correct (b > c).

### 4.4 Sensitivity Analysis (FR-006)
- **Metric**: "Inconsistency Tolerance" (Levenshtein edit distance).
- **Granularity**: Action sequences are serialized strings (e.g., "tap(10,20)"); Levenshtein distance is applied at the **character level** to ensure metric validity for tokenized strings.
- **Procedure**: Sweep thresholds (e.g., 0, 1, 2, 3) and measure variance in success rates.
- **Reporting**: Variance across thresholds, avoiding hard pass/fail cutoffs (SC-005).

### 4.5 Ablation Study (Constitution Principle VII)
- **Condition**: Replace `Corrective_Hint` with a generic "retry" prompt.
- **Goal**: Verify that performance gains are due to the specific hint content, not just additional context.
- **Alignment**: The primary evaluation metric is "Success with Hint" (testing hint utilization). The ablation tests "Success without Hint" (testing generalization). The research hypothesis is supported if the model maintains reasonable performance in the ablation condition, demonstrating transferable reasoning.

## 5. Compute Feasibility & Data Availability

### 5.1 CPU Feasibility
- **Training**: T5-small (~60M params) on CPU is feasible within 6 hours for ~100k samples using standard `transformers` training loops with small batch sizes.
- **Inference**: CPU inference for T5-small is fast (<1s per task).
- **Escape Hatch**: If T5-small training exceeds time limits, the plan allows for a **smaller subset** of the training data (e.g., 10k samples) rather than switching to a GPU, as the research question is about CPU tractability. The pilot feasibility check (Phase 3) will trigger this contingency if needed.

### 5.2 Data Availability
- **Training Data**: MobileForge logs are available via verified GitHub repositories or HuggingFace datasets. No credentials required.
- **Evaluation Data**: AndroidWorld tasks are available via the official GitHub repository (`google-deepmind/androidworld`) with programmatic access.

## 6. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **T5-small over DistilBERT** | Task is sequence generation; Encoder-Decoder is native. |
| **McNemar's over t-test** | Data is binary (Success/Fail); t-test is invalid. |
| **A Priori over Post-hoc** | Post-hoc is tautological; A priori ensures study power. |
| **CPU-only** | Core research hypothesis: reasoning is transferable without visual/GPU retraining. |
| **Levenshtein for Sensitivity** | Provides a continuous metric for "closeness" of action sequences. |
| **Pilot for p0** | Ensures power analysis is based on empirical baseline performance, not arbitrary assumptions. |
| **Input Parity** | Ensures fair comparison between T5 and TinyLlama by controlling for input context. |
| **Control Group** | Prevents overfitting to error recovery by including "initial success" trajectories. |