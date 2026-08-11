# Model Selection Decision Log

## Objective
To determine the optimal non-neural model (Decision Tree vs. CGMM) for approximating VLA priors per cluster.

## Selection Strategy
As per the project specification (FR-002a / T022), the pipeline employs a sequential evaluation and selection process to ensure computational efficiency and adherence to performance constraints.

## Selection Criteria
The primary selection criteria is defined as follows:

**highest R² on held-out validation set, provided inference time < 2s per prompt**

The process for each cluster is:
1. **Train Decision Tree**: Fit a Decision Tree regressor mapping BERT embeddings to actions.
2. **Evaluate DT**: Calculate R² on the held-out set and measure inference time.
3. **Check Thresholds**:
 - If R² >= 0.6 AND inference time < 2s/prompt: **Select Decision Tree**. Stop training for this cluster.
 - Else: Proceed to train the Conditional Gaussian Mixture Model (CGMM).
4. **Train CGMM (Fallback)**: If DT fails the thresholds, train a CGMM.
5. **Evaluate CGMM**: Calculate R². If R² >= 0.6, select CGMM.
6. **Failure Handling**: If neither model meets the R² >= 0.6 threshold, log a "Model Failure" warning and select the model with the highest available R².

## Rationale
- **Decision Trees** are prioritized as the primary candidate due to their computational efficiency and ability to capture non-linear boundaries with low latency.
- **CGMMs** serve as a robust fallback for clusters where the action distribution is multi-modal or the Decision Tree fails to achieve the required explanatory power (R² >= 0.6).
- The **2s/prompt** constraint ensures the system meets real-time inference requirements on CPU-only hardware.
- This sequential approach minimizes computational cost by avoiding training both models for every cluster unless necessary.

## Output Artifacts
- `artifacts/models/cluster_{id}_selected.pkl`: The final selected model (DT or CGMM).
- `artifacts/models/cluster_{id}_selection.json`: JSON file containing:
 - `selected_model_type`: "DecisionTree" or "CGMM"
 - `dt_r2`: R² score of the Decision Tree
 - `cgmm_r2`: R² score of the CGMM (if trained)
 - `dt_inference_time_ms`: Inference time for DT
 - `selection_reason`: Explanation of why the model was chosen (e.g., "DT met thresholds", "CGMM fallback due to low DT R²")

## Summary
The pipeline dynamically adapts to the characteristics of each behavioral cluster. The selection is driven strictly by the **highest R² on held-out validation set, provided inference time < 2s per prompt**, ensuring a balance between predictive accuracy and operational efficiency.