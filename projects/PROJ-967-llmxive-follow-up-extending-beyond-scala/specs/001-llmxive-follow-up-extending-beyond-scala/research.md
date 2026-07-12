# Research: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Research Question

Does the "structural entanglement" (statistical spread and dimension dependency) of a teacher model's multi-dimensional score distribution predict the "dimensional fidelity loss" incurred when distilling to a scalar student model?

## Dataset Strategy

### Verified Datasets
The analysis relies on the **Z-Reward** evaluation dataset.
- **Source**: Verified HuggingFace dataset `z-reward` (or equivalent verified archive referenced in the spec).
- **Content**: Prompts, generated images, human annotations (4 dimensions: Alignment, Realism, Aesthetics, Plausibility), and pre-computed inference outputs (logits/scores) for teacher (27B) and student (9B) models.
- **Access**: Loaded via `datasets.load_dataset("z-reward")` or direct CSV/JSON ingestion if raw files are provided in the repo.

### Dataset-Variable Fit Verification
- **Required Variables**:
  - `teacher_scores`: Array of 4 floats (Alignment, Realism, Aesthetics, Plausibility).
  - `student_scores`: Scalar float.
  - `human_annotations`: Array of 4 floats (ground truth).
  - `primary_dimension_id`: Metadata indicating which dimension is the "primary quality attribute" for the sample.
- **Fit Check**: The ingestion script (`code/ingest.py`) will explicitly verify that every sample contains valid entries for all four dimensions in both `teacher_scores` and `human_annotations`. 
- **Data Availability Check**: If the dataset lacks pre-computed `teacher_scores` or `student_scores`, the pipeline will halt with a "Data Gap" error. We do not generate these scores via LLM inference due to resource constraints.
- **Constraint**: If the verified dataset lacks the `primary_dimension_id` metadata, the plan will default to using the **Alignment** dimension (the first in the schema) for all samples as a deterministic fallback, while noting this limitation in the report.

## Methodology

### Phase 1: Data Ingestion & Preprocessing (FR-001, FR-006)
1. Load Z-Reward dataset.
2. Align teacher scores, student scores, and human annotations by sample ID.
3. **Filtering**: Exclude samples where human annotations are missing for the target dimension.
4. **Normalization**: Ensure scores are on a consistent scale (e.g., 0-1 or 0-100) across teacher and human annotations.
5. **Validation**: Check for the existence of required score fields. If missing, raise a blocking error.

### Phase 2: Feature Engineering (FR-002, Principle VI)
For each sample, compute "Entanglement Features" from the teacher's 4-dimensional score vector $T = [t_1, t_2, t_3, t_4]$:
1. **Variance**: $\text{Var}(T)$.
2. **Range (Spread)**: $\max(T) - \min(T)$. (Replaces Entropy, which is invalid for independent metrics).
3. **Standard Deviation**: $\sigma(T)$.
4. **Skewness & Kurtosis**: Statistical moments of the distribution.
5. **Global Covariance Eigenvalue**: Calculate the covariance matrix $C$ of the *entire dataset's* teacher scores (N samples). Compute the dominant eigenvalue $\lambda_{max}$ of $C$. This value is **constant** for all samples and represents the global structural dependency of the dimensions.
   - *Correction*: We do **not** calculate a covariance matrix per sample (N=1 is impossible). The per-sample feature is the variance/range of the 4 scores. The eigenvalue is a global context feature.
6. **Zero-Variance Handling**: If $\text{Var}(T) = 0$, set Range to 0.

### Phase 3: Target Variable Construction (FR-003, Principle VII)
1. **Primary Dimension Selection**: If `primary_dimension_id` exists, use it. Otherwise, default to "Alignment".
2. **Construct Validity Check**: Verify if the student scalar is intended to predict the specific dimension or a generic aggregate.
   - If the student scalar is a generic reward, the target is redefined as $L = |S_{pred} - \text{Avg}(H_{human})|$ to avoid comparing a generic score to a specific dimension (construct validity failure).
3. **Fidelity Loss Calculation**: Compute $L = |S_{pred} - H_{target}|$.
   - *Circularity Mitigation*: If the student scalar is a deterministic function of the teacher scores (e.g., $S = \text{WeightedSum}(T)$), the analysis focuses on the *residual* error against human annotations, acknowledging that the model may learn the deterministic mapping rather than structural entanglement.

### Phase 4: Predictive Modeling (FR-004, FR-005)
1. **Dimensionality Reduction**: Apply PCA to the entanglement features to orthogonalize collinear metrics (Variance, Range, Skewness) before training.
2. **Model**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
3. **Hyperparameters**: Default `scikit-learn` settings (optimized for CPU).
4. **Validation**: 5-fold Cross-Validation.
5. **Metrics**:
   - **R² Score**: Coefficient of determination (measuring *associational* power).
   - **MAE**: Mean Absolute Error of the cross-validated predictions.
   - **Permutation Test**: Calculate p-value to test significance of feature importance.
6. **Null Baseline**: Compare against a model that predicts the mean loss.

## Statistical Rigor & Feasibility

### Statistical Rigor
- **Multiple Comparisons**: Only one primary hypothesis is tested. If multiple models are run, Bonferroni correction will be applied.
- **Power Analysis**: Post-hoc power analysis will be reported. If $N < 1000$, the study is framed as exploratory.
- **Causal Claims**: The study is **observational**. Claims are strictly **associational**. No causal inference ("entanglement causes loss") will be made.
- **Collinearity**: PCA is used to reduce collinearity among derived features. Feature importance is interpreted cautiously.

### Compute Feasibility (Free-Tier CI)
- **Memory**: Data will be loaded in chunks if $> 5$GB. Random Forest on $< 50k$ samples with 5-10 features fits easily in 7GB RAM.
- **CPU**: `scikit-learn` Random Forest is highly optimized for CPU. 5-fold CV on a moderate dataset will complete in < 1 hour on 2 cores.
- **No GPU**: No CUDA dependencies.
- **Time**: Total pipeline < 2 hours.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Random Forest** | Non-parametric, handles non-linear relationships, robust to outliers, CPU-efficient. |
| **PCA Pre-processing** | Mitigates collinearity among derived statistical features (Variance, Range, etc.) for stable feature importance. |
| **Global Eigenvalue** | Correctly measures dimension dependency without violating N=1 statistical constraints. |
| **Entropy Removal** | Shannon Entropy is invalid for independent rubric scores; replaced by Range and StdDev. |
| **Exclusion of Missing Data** | Prevents imputation bias; ensures target variable is strictly based on verified human ground truth. |

## Risks & Mitigations

- **Risk**: Z-Reward dataset lacks `primary_dimension_id` or pre-computed scores.
  - *Mitigation*: Default to "Alignment" for dimension; halt with "Data Gap" if scores are missing.
- **Risk**: Dataset size > 7GB RAM.
  - *Mitigation*: Implement chunked loading and sampling.
- **Risk**: Circular validation (Student = f(Teacher)).
  - *Mitigation*: Explicitly frame results as "human-aligned residual error" and acknowledge the limitation in the report.