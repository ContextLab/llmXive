# Model Selection Decision Log

## Objective
To determine the optimal non-neural model (Decision Tree vs. CGMM) for approximating VLA priors per cluster.

## Selection Strategy
As per the project specification (FR-002a / T022b), the pipeline does not arbitrarily choose one model type. Instead, it employs a **comparative analysis**:

1. **Dual Training**: For every cluster identified in the clustering phase, both a Decision Tree (DT) and a Conditional Gaussian Mixture Model (CGMM) are trained.
2. **Evaluation**: Both models are evaluated on a held-out validation set specific to that cluster.
3. **Metric**: The **R² score** (Coefficient of Determination) is used as the primary performance metric.
4. **Selection Rule**:
 - The model with the **higher R² score** is selected as the final approximation for that cluster.
 - If `R²_DT > R²_CGMM`, the Decision Tree is selected.
 - Otherwise, the CGMM is selected.

## Rationale
- **Decision Trees** excel at capturing sharp, non-linear boundaries and are computationally efficient for inference.
- **CGMMs** are superior at modeling multi-modal distributions and uncertainty, which are common in robotic tasks where multiple valid trajectories exist for a single instruction.
- By comparing them empirically, the pipeline adapts to the specific characteristics of each behavioral cluster (e.g., a "grasp" cluster might be multi-modal favoring CGMM, while a "navigate" cluster might be deterministic favoring DT).

## Output Artifacts
- `artifacts/models/cluster_{id}_dt.pkl`: Trained Decision Tree (kept for comparison).
- `artifacts/models/cluster_{id}_cgmm.pkl`: Trained CGMM (kept for comparison).
- `artifacts/models/cluster_{id}_selection.json`: JSON file containing the R² scores of both models and the ID of the selected model.

## Future Considerations
If the R² scores are within a negligible margin (e.g., < 0.01 difference), the pipeline defaults to the **Decision Tree** due to its lower inference latency, unless the CGMM provides significantly better uncertainty calibration (to be measured in future iterations).