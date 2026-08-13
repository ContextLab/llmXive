# Research: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

## 1. Research Objective

To quantify the "modality gap" in physical AI world models by comparing the performance of a lightweight symbolic reasoning proxy model against an independent continuous control baseline. Specifically, we investigate whether the discretization of continuous action vectors into symbolic tokens leads to a statistically significant degradation in predictive accuracy (generalization loss), and we characterize the nature of the resulting failure modes.

**Key Refinement**: The "modality gap" is now defined as the performance drop of the **Symbolic Model** when evaluated on the **Physics Task** (cross-domain generalization), compared to its performance on the **Symbolic Task**. This avoids the circularity of comparing a model to itself on different ground truths without a valid mapping. The Physics Task uses the **independent physics_reward** from the dataset, ensuring the ground truth is not derived from the same action vector used for the Symbolic label.

**Construct Validity Note**: To address concerns about triviality, the Symbolic Label is not derived from a simple scalar threshold alone. It is a **composite rule** involving the L2 norm of the first 3 dimensions of the action vector AND the semantic context of the text description (simulating a "Safety Constraint"). This ensures the model must learn a relationship between multimodal inputs and the constraint, rather than just a mathematical identity, preventing the "gap" from being an artifact of task difficulty.

## 2. Dataset Strategy

### 2.1 Target Dataset: Bridge (Verified Substitute)
The primary target is the **Bridge** dataset (from the Bridge-to-Worlds paper), which is publicly available on Hugging Face and contains continuous action vectors and physics rewards.
- **Source**: `https://huggingface.co/datasets/bridge-to-worlds/bridge-data`
- **Status**: **Verified**. Contains `action` vectors (list of floats, length >= 3) and `physics_reward` fields.
- **Implication**: This dataset supports the core scientific question (continuous -> symbolic transformation) and is accessible via `datasets.load_dataset`.
- **Fallback**: If the Bridge dataset is unavailable or lacks required fields (`action` with length >= 3, `physics_reward`), the pipeline **ABORTS** with a clear error. No synthetic data or invalid substitutes (e.g., text-only datasets) are used.

### 2.2 Data Loading Strategy
- **Streaming**: `datasets.load_dataset(..., streaming=True)` will be used to iterate over shards without loading the full dataset into RAM (addressing the 7 GB limit).
- **Sampling**: If the full dataset exceeds memory, a fixed-seed random sample (e.g., first [deferred] rows) will be extracted and stored locally with a checksum.
- **Schema Verification**: Before processing, the pipeline explicitly checks the first N samples for the presence of `action` (list of floats, length >= 3) and `physics_reward` (float). If missing, the pipeline aborts.

## 3. Methodology

### 3.1 Data Transformation (FR-001, FR-002)
- **Input**: Continuous action vectors (e.g., `[x, y, z, ...]`) and `physics_reward` (float).
- **Symbolic Label Rule (Composite)**:
  1. Calculate `L2 norm` of the first 3 dimensions (x, y, z) of the `action_vector`.
  2. Check `text_description` for keywords indicating "collision", "unsafe", or "constraint" (simulated safety context).
  3. If `norm > 0.5` AND `context_match == True` -> `constraint_violated`.
  4. Else -> `constraint_satisfied`.
  - *Rationale*: This composite rule ensures the task is non-trivial (construct validity). A simple norm threshold would be a scalar identity; adding the text context requires the model to learn a multimodal logical relationship.
- **Physics Label Rule**: `physics_reward > 0.5` -> `success`, else `failure`.
  - *Note*: This rule is **independent** of the Symbolic label rule. The `physics_reward` is derived from the simulator's internal state, not the action norm, ensuring the two ground truths are not circularly correlated.
- **Output**: A JSONL/CSV file with original inputs, `symbolic_label`, and `physics_label`.

### 3.2 Symbolic Proxy Training (FR-003, FR-004)
- **Model**: `DistilBERT-base-uncased` trained on `symbolic_label`.
- **Constraints**:
  - Batch size tuned dynamically to stay under 7 GB RAM.
  - Mixed precision (FP16) disabled if it causes instability on CPU; default FP32 used.
  - Max 6 hours runtime.

### 3.3 Comparative Analysis (FR-004, FR-005)
- **Domains**:
  1. **Symbolic Task**: Accuracy/F1/AUC on the `symbolic_label` (trained model).
  2. **Physics Task (Cross-Domain)**: Accuracy/F1/AUC on the `physics_label` (trained Symbolic Model).
- **Statistical Test**: **Bootstrap Confidence Interval** (1000 iterations) on the **Generalization Gap** (`AUC_Symbolic - AUC_Physics_CrossDomain`).
  - *Rationale*: This test measures the "generalization loss" (modality gap) by comparing the model's performance on its training domain vs. the cross-domain task. It avoids the category error of comparing AUCs of different ground truths directly.
  - *Significance*: If the 95% CI of the gap does not include 0, the degradation is statistically significant.

### 3.4 Error Analysis (FR-006)
- **Taxonomy**:
  1. **Visual Ambiguity**: Errors correlated with low-contrast or occluded video frames.
  2. **Logical Complexity**: Errors on samples with high-dimensional action vectors or complex constraint interactions.
  3. **Context Mismatch**: Errors where the text description contradicts the action.
- **Method**: Feature importance analysis (SHAP or attention weights) on misclassified samples.

## 4. Compute Feasibility & Rationale

- **CPU-First**: The plan uses DistilBERT and classical statistics, which are tractable on a limited-core CPU with constrained RAM.
- **GPU Escape Hatch**: Not required for this specific proxy model. If the dataset size forces a larger model, the plan would switch to a scaled-down version or offload to Kaggle (as per the "GPU escape hatch" rule), but the current spec mandates a "lightweight" model.
- **Data Streaming**: Essential for handling datasets larger than RAM. The pipeline will stream data, compute statistics online, and only load batches for training.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Bridge Dataset Unavailable** | Fatal (No data) | Script checks for verified URL; if missing, exits with clear error. No synthetic data generation. |
| **Schema Mismatch** | Fatal (Incorrect labels) | T002 explicitly checks for `action` (len>=3) and `physics_reward` fields. Exits if missing. |
| **Memory Exceeds 7 GB** | Fatal (OOM) | Use `streaming=True`; implement batch processing; sample data if necessary. |
| **Model Fails to Converge** | Medium (No results) | Increase epochs; adjust learning rate; fallback to a simpler logistic regression baseline for comparison. |
| **Ambiguous Action Vectors** | Medium (Label noise) | Define explicit handling for missing/NaN vectors (e.g., exclude or default label) and document the rule. |
| **Trivial Rule** | Medium (Invalid construct) | Use "Safety Constraint Simulation" (norm + text context) for Symbolic label to ensure non-triviality. |

## 6. Decision Rationale

- **Why DistilBERT?** It provides a balance between transformer expressiveness and CPU efficiency. Full BERT or larger models would likely exceed the available RAM limit or the time budget on CPU.
- **Why L2 Norm of First 3 Dims + Text Context?** This is a deterministic threshold derived from the spec, ensuring reproducibility. The "Safety Constraint Simulation" adds complexity to avoid triviality and ensures the model learns a multimodal relationship.
- **Why No GPU?** The research question focuses on the *representational* gap, not computational power. A CPU-only proxy isolates the modality issue without the confounding factor of GPU acceleration.
- **Why Bootstrap CI?** It is the appropriate test for comparing the performance drop (generalization loss) of a single model across two different domains, avoiding the statistical invalidity of comparing AUCs of different ground truths.