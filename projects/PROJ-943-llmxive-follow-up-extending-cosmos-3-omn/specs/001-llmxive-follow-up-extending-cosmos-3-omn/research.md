# Research Report: llmXive Follow-up - Extending "Cosmos 3: Omnimodal World Models for Physical AI"

## Executive Summary

This research initiative, **llmXive**, investigates the "modality gap" in Physical AI world models by pivoting from the originally proposed Cosmos 3 dataset to the **Bridge Data** (Bridge-to-Worlds) dataset. The primary objective is to determine if continuous action vectors from real-world robotic interactions can be effectively transformed into discrete symbolic tokens to enable efficient, CPU-compatible proxy models for safety reasoning.

Our hypothesis is that a significant performance gap exists between a model's ability to reason about symbolic constraints (e.g., "Safety Constraint") versus continuous physical rewards (e.g., `physics_reward`), and that this gap can be quantified using statistical significance testing and error analysis.

## 1. Data Source Pivot: From Cosmos 3 to Bridge Data

### 1.1 Original Proposal (Cosmos 3)
The initial project design referenced **Cosmos 3: Omnimodal World Models for Physical AI** as the primary data source. Cosmos 3 represents a large-scale, multimodal dataset intended for training world models capable of reasoning about physics, language, and actions. However, during the feasibility analysis phase (Phase 2), it was determined that:
1. **Availability**: The full Cosmos 3 dataset is not yet publicly accessible via a standard, programmatic interface (e.g., Hugging Face `datasets`) suitable for streaming in a constrained environment.
2. **Schema Complexity**: The specific action vector structure and reward signals required for our "modality gap" analysis were not guaranteed to be present in the public preview.

### 1.2 Pivot Rationale
Consequently, the project has pivoted to the **Bridge Data** (`bridge-to-worlds/bridge-data`) hosted on Hugging Face. This pivot was driven by:
* **Immediate Availability**: The dataset is publicly available and supports `streaming=True` for memory-efficient processing.
* **Schema Compatibility**: The dataset contains the necessary fields: `actions` (continuous vector), `text_description` (natural language context), and `physics_reward` (continuous physical outcome signal).
* **Representativeness**: While distinct from Cosmos 3, Bridge Data provides sufficient real-world robotic interaction samples to validate the hypothesis regarding the symbolic-physical modality gap.

### 1.3 Data Characteristics
The Bridge Data dataset is processed using the following configuration:
* **Source**: `bridge-to-worlds/bridge-data`
* **Streaming Mode**: Enabled (`streaming=True`) to adhere to the < 7 GB RAM constraint.
* **Key Fields**:
 * `actions`: A continuous vector representing robot end-effector commands.
 * `text_description`: A string describing the task or context.
 * `physics_reward`: A scalar float indicating physical success/efficiency.
 * `observation`: Visual or proprioceptive data (used for context validation).

## 2. Methodology

### 2.1 Symbolic Transformation Pipeline
The core methodological contribution is the transformation of continuous action vectors into discrete symbolic tokens. This process is defined by a composite logical rule stored in `code/data/schema/action_schema.json`.

**The Transformation Logic:**
1. **L2 Norm Calculation**: Compute the L2 norm of the **first 3 dimensions** of the `actions` vector.
 $$ \text{norm} = \sqrt{\sum_{i=1}^{3} \text{actions}[i]^2} $$
2. **Text Keyword Matching**: Check if the `text_description` contains the keyword "Safety Constraint".
3. **Composite Rule Application**:
 * **Threshold**: `norm > 0.5`
 * **Composite Condition**: `(norm > 0.5) AND ("Safety Constraint" in text_description)`
 * **Labeling**:
 * If composite condition is **True**: Label = `constraint_violated`
 * If composite condition is **False**: Label = `constraint_satisfied`

This schema adaptation (T004, T010) replaces the original Cosmos 3-based heuristic, allowing us to ground symbolic reasoning in measurable physical properties of the action vector.

### 2.2 Proxy Model Training (Hard Proxy)
To test the hypothesis, we train a **DistilBERT** model (CPU-compatible) to predict the symbolic label (`constraint_violated` vs `constraint_satisfied`) derived from the transformation pipeline.
* **Input**: `text_description` and normalized `actions`.
* **Target**: The symbolic label.
* **Constraint**: Training must complete within 6 hours on CPU with < 7 GB RAM.
* **Output**: A model artifact (`code/models/proxy_hard/model.pt`) capable of symbolic reasoning.

### 2.3 Comparative Performance Analysis (The Modality Gap)
The central analysis compares the model's performance on the **Symbolic Domain** vs. the **Physical Domain**.

1. **Symbolic Domain**: Performance measured against the derived symbolic labels (T010).
2. **Physical Domain**: Performance measured against the continuous `physics_reward` threshold (e.g., `reward > 0.5` -> success).
3. **Metrics**:
 * Accuracy, F1-Score, AUC-ROC, Brier Score.
4. **Statistical Significance**:
 * **Normality Test**: Shapiro-Wilk test on the difference of metrics (Symbolic - Physical).
 * **Significance Test**: Paired t-test (if normal) or Wilcoxon signed-rank test (if non-normal).
 * **Confidence Interval**: Bootstrap CI (1000 iterations) on the Generalization Gap ($AUC_{symbolic} - AUC_{physical}$).

### 2.4 Error Analysis & Failure Modes
Misclassified samples are extracted and categorized into three specific failure modes to understand the limitations of the proxy model:
1. **Visual Ambiguity**: Low model confidence (< 0.6) or missing observation data.
2. **Logical Complexity**: Conflict between the L2 norm and text keyword (e.g., high norm but no keyword).
3. **Context Mismatch**: Text explicitly states "Safety Constraint" but the action vector contradicts this (or is zero).

## 3. Implementation Details

### 3.1 Infrastructure
* **Language**: Python 3.9+
* **Libraries**: `datasets`, `transformers`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib`.
* **Memory Management**: All data loading uses `streaming=True` to prevent OOM errors. Memory usage is monitored via `tracemalloc` and `psutil`.

### 3.2 Artifacts
The pipeline produces the following key artifacts:
* `code/data/raw/bridge_samples.jsonl`: Raw streamed data.
* `code/data/processed/unified_dataset.jsonl`: Labeled dataset with symbolic and physical tags.
* `code/models/proxy_hard/model.pt`: Trained DistilBERT proxy model.
* `code/data/results/raw_predictions.jsonl`: Inference results with confidence scores.
* `code/data/results/gap_metrics.json`: Calculated generalization gap.
* `code/data/results/comparative_analysis.json`: Statistical test results (p-value, bootstrap CI).
* `code/data/processed/misclassified_samples.jsonl`: Extracted errors for analysis.
* `code/data/results/error_analysis_report.md`: Qualitative and quantitative error report.
* `code/data/results/error_visualizations.png`: Scatter plot of error rates vs. feature magnitude.

## 4. Results & Discussion

*Note: The following sections describe the expected outcomes and the methodology for validating them.*

### 4.1 Quantitative Findings
We anticipate a statistically significant **Generalization Gap**, where the model performs significantly better on the Symbolic Domain (derived from clear text/norm rules) than on the Physical Domain (derived from noisy `physics_reward` signals).
* **Hypothesis**: $AUC_{symbolic} > AUC_{physical}$ with $p < 0.05$.
* **Evidence**: The `comparative_analysis.json` artifact will contain the computed `p_value` and `is_significant` flag derived from the Shapiro-Wilk -> t-test/Wilcoxon sequence.

### 4.2 Error Mode Distribution
The error analysis is expected to show that **Logical Complexity** is the primary failure mode, indicating that the simple composite rule (Norm + Keyword) does not fully capture the nuance of the "Safety Constraint" concept in the text, leading to misalignment between the symbolic label and the physical reality.

### 4.3 Implications for Physical AI
If the modality gap is confirmed, it suggests that current world models may be over-reliant on continuous physical signals and lack robust symbolic grounding. The proposed "Hard Proxy" approach offers a lightweight mechanism to inject symbolic constraints into physical AI pipelines, potentially improving safety and interpretability.

## 5. Conclusion

This research successfully pivoted from the inaccessible Cosmos 3 dataset to the publicly available Bridge Data, adapting the methodology to utilize L2 norms and text keyword matching for symbolic transformation. The pipeline is designed to rigorously quantify the gap between symbolic reasoning and physical control, providing actionable insights for the development of safer, more interpretable Physical AI systems.

Future work will involve expanding the symbolic rule set, incorporating more complex visual features, and testing the proxy model in a real-time control loop.

## 6. References

1. **Bridge Data**: "Bridge Data: A Large-Scale Dataset for Robot Learning from Human Demonstrations" (Hugging Face: `bridge-to-worlds/bridge-data`).
2. **Cosmos 3**: "Cosmos 3: Omnimodal World Models for Physical AI" (NVIDIA).
3. **DistilBERT**: Sanh, V., et al. "DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter." (2019).
4. **Scikit-learn**: Pedregosa, F., et al. "Scikit-learn: Machine Learning in Python." (2011).
5. **Hugging Face Datasets**: Lhoest, Q., et al. "Datasets: A Community Library for Natural Language Processing." (2021).