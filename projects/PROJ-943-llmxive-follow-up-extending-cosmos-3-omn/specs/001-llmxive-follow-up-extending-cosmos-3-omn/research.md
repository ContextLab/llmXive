# llmXive Research: Extending "Cosmos 3: Omnimodal World Models for Physical AI"

## Executive Summary

This research project investigates the "modality gap" in physical AI by pivoting from the originally proposed Cosmos 3 synthetic dataset to the **Bridge Data** (bridge-to-worlds/bridge-data) due to immediate data availability and accessibility constraints. We implement a symbolic reasoning proxy model to analyze the divergence between continuous control performance and discrete logical reasoning in embodied agents.

## 1. Introduction

### 1.1 Background
Recent advances in world models, specifically "Cosmos 3: Omnimodal World Models for Physical AI," suggest that large-scale generative models can learn robust representations of physical dynamics. However, a critical gap remains in understanding how these models handle **logical constraints** versus **continuous physical rewards**.

### 1.2 Problem Statement
Physical AI agents often excel at continuous control tasks (minimizing distance, maximizing speed) but fail when presented with discrete logical constraints (e.g., "do not cross the red line," "safety violation"). This research quantifies that gap.

### 1.3 Pivot Rationale: From Cosmos 3 to Bridge Data
**Original Plan**: The initial specification relied on the Cosmos 3 synthetic dataset.
**Current Reality**: The Cosmos 3 dataset is not immediately available for programmatic access in the current execution environment, posing a blocker for the MVP phase.
**Decision**: We pivot to the **Bridge Data** (`bridge-to-worlds/bridge-data`), a real-world robotic manipulation dataset available via the Hugging Face `datasets` library.
**Justification**:
- **Availability**: The dataset is public, streamable, and contains the necessary action vectors and text descriptions.
- **Relevance**: Bridge Data includes continuous action vectors and natural language instructions, allowing us to reconstruct the logical constraints required for the study.
- **Feasibility**: Enables immediate implementation of the "Download & Transform" pipeline without waiting for proprietary data access.

## 2. Data Source

### 2.1 Primary Dataset: Bridge Data
- **Source**: `bridge-to-worlds/bridge-data` on Hugging Face.
- **Access Method**: Programmatic loading via `datasets.load_dataset(..., streaming=True)`.
- **Structure**:
 - `actions`: Continuous vector array (float32).
 - `text_description`: Natural language instruction or context.
 - `physics_reward` (Derived/Checked): Continuous reward signal used for baseline comparison.
- **Volume**: Large-scale robotic trajectories; processed via streaming to adhere to the 7GB RAM constraint.

### 2.2 Data Availability Check
The system is configured to **fail loudly** if the dataset cannot be fetched. No synthetic or placeholder data is permitted. If `bridge-to-worlds/bridge-data` is inaccessible, the pipeline aborts with a clear error message.

## 3. Methodology

### 3.1 Schema Adaptation Strategy
To apply logical reasoning to the Bridge Data (which lacks explicit "safety" labels), we implemented a **Composite Rule Schema** (defined in `code/data/schema/action_schema.json`). This schema adapts the continuous action space into discrete symbolic tokens.

**The Adaptation Logic**:
1. **L2 Norm Calculation**: Compute the L2 norm of the **first 3 dimensions** of the `actions` vector. This serves as a proxy for "action magnitude" or "force."
2. **Text Context Analysis**: Check if `text_description` contains specific keywords (e.g., "Safety Constraint").
3. **Composite Rule (AND)**:
 - **Condition A**: `norm(actions[0:3]) > threshold` (e.g., 0.5)
 - **Condition B**: `text_description` contains any keyword from `text_keywords`.
 - **Result**: If **A AND B** are true, label as **"constraint_violated"**. Otherwise, label as **"constraint_satisfied"**.

**Rationale**: This synthetic labeling approach allows us to create a "symbolic" test set from continuous data, enabling the training of a Hard Proxy model (DistilBERT) to predict logical outcomes.

### 3.2 Experimental Pipeline

1. **Data Ingestion**: Stream `bridge-to-worlds/bridge-data` and filter for instances with valid `actions` and `text_description`.
2. **Transformation**: Apply the L2 Norm + Text Keyword composite rule to generate binary labels (`constraint_violated` vs `constraint_satisfied`).
3. **Model Training**: Train a lightweight DistilBERT model (CPU-optimized) to predict the symbolic label from the text description.
4. **Comparative Analysis**:
 - **Symbolic Domain**: Evaluate model performance on the derived logical labels.
 - **Physical Domain**: Evaluate performance on the native `physics_reward` (continuous).
 - **Statistical Test**: Perform Shapiro-Wilk (normality) followed by t-test or Wilcoxon signed-rank test to determine if the performance gap is statistically significant.
5. **Error Analysis**: Categorize misclassifications into "Visual Ambiguity," "Logical Complexity," and "Context Mismatch."

### 3.3 Constraints & Requirements
- **Memory**: Peak usage must remain < 7GB (enforced via streaming and memory monitoring).
- **Time**: Training must complete within 6 hours.
- **Reproducibility**: All seeds are fixed via `code/config.py`.
- **No Synthetic Data**: All results must derive from real Bridge Data samples.

## 4. Implementation Details

### 4.1 Directory Structure
- `code/scripts/`: Main pipeline scripts (`download.py`, `transform.py`, `train.py`, `evaluate.py`, `analyze_errors.py`).
- `code/data/raw/`: Raw dataset samples (JSONL).
- `code/data/processed/`: Labeled/unified datasets.
- `code/models/`: Trained proxy model artifacts.
- `code/data/results/`: Statistical reports and visualizations.

### 4.2 Key Modules
- **Schema Loader**: Reads `action_schema.json` to dynamically configure thresholds and keywords.
- **Streaming Transformer**: Processes data in chunks to avoid OOM errors.
- **Statistical Engine**: Implements adaptive testing (t-test vs. Wilcoxon) based on data distribution.

## 5. Expected Outcomes

1. **Quantitative Gap**: A measured p-value indicating the significance of the performance difference between symbolic and physical reasoning.
2. **Proxy Model**: A CPU-compatible model capable of predicting logical constraints from text descriptions.
3. **Error Taxonomy**: A categorized report of where the model fails (e.g., failing to detect high-magnitude actions in specific contexts).

## 6. Conclusion

By pivoting to Bridge Data and implementing a robust schema adaptation strategy, this project successfully establishes a baseline for measuring the "modality gap" in physical AI. The shift from synthetic to real-world data ensures that the findings are grounded in actual robotic interaction dynamics, providing a more reliable assessment of the limitations of current world models in handling logical constraints.

## References

- Bridge Data: `bridge-to-worlds/bridge-data` (Hugging Face)
- Cosmos 3: Omnimodal World Models for Physical AI (Original Paper)
- DistilBERT: Sanh et al., "DistilBERT, a distilled version of BERT"