# Research: Predicting Material Degradation Pathways from Compositional Data

## Dataset Strategy

**Critical Finding**: The project spec mandates the use of **public Zenodo corrosion datasets** containing metallic alloys with elemental composition and degradation labels. The specific Zenodo DOI cited in the spec (e.g., ``) is the primary source to verify. The 'Verified datasets' block in the project inventory is a secondary check and does not preclude the use of the Zenodo source.

**Action Plan**:
1. **Primary Attempt**: The `ingestion.py` script will attempt to fetch the specific Zenodo DOI (``) referenced in the spec.
2. **Verification**: If the DOI is unreachable or the data format does not match the "Verified datasets" criteria (i.e., if the Zenodo source is not valid), the system will **halt execution** with a `DatasetUnreachableError` and a clear message.
3. **Fallback**: No fallback to the provided NLP datasets is permitted, as they lack the required features (elemental composition, degradation pathways). Using them would violate **FR-001** and **Dataset-variable fit**.

*Note: If the Zenodo source is confirmed reachable and valid during the `research` phase, the URL will be added to the verified list. For this plan, we assume the Zenodo source is the intended target.*

**Hypothetical Dataset Structure (if Zenodo source is valid):**
| Source | Format | Content | Status |
|:--- |:--- |:--- |:--- |
| Zenodo Corrosion Repo () | CSV/Parquet | Elemental wt%, Degradation Label | **Target** (Requires verification) |
| *N/A (Provided Block)* | *Parquet/Gzip* | *Text/NLP* | *Incompatible* |

## Methodology

### 1. Data Ingestion & Filtering (FR-001, FR-002)
- **Filter**: Retain only records where `material_type == "metallic_alloy"`. Remove polymers/composites.
- **Imputation**:
 - Calculate missingness per record for elemental fields.
 - If missing < 5%: Impute with **median value per element** (calculated from the full dataset).
 - If missing ≥ 5%: Exclude record.
- **Feature Encoding**:
 - **Primary Features**: Elemental weight percentages (normalized to sum to [deferred]).
 - **Derived Features**: Electronegativity, atomic radius (mapped from periodic table) calculated for post-hoc analysis only. **Excluded** from training vector to prevent multicollinearity (FR-002).

### 2. Train/Test Split (FR-007)
- **Strategy**: **Class-Based Out-of-Distribution (OOD) Split**.
- **Logic**: Identify distinct alloy classes (e.g., "Stainless Steel", "High-Entropy Alloy", "Aluminum Alloy").
- **Split**: Hold out entire classes (e.g., all High-Entropy Alloys) as the **Test Set**. The remaining classes form the **Training Set**.
- **Contingency**: If the dataset lacks sufficient class diversity (e.g., only one alloy class exists), fall back to a **Stratified Random Split** and explicitly flag the inability to test generalization to new classes in the final report.
- **Rationale**: Validates generalization to unseen material families, not just unseen samples from known families.

### 3. Model Training (FR-003)
- **Algorithm**: Random Forest Classifier (Multi-label).
- **Hardware**: CPU-only (scikit-learn default).
- **Parameters**: `n_estimators=100`, `max_depth=None` (or constrained by time), `random_state=42`.
- **Constraint**: Must complete within 6 hours on 2 CPU cores.

### 4. Evaluation & Statistical Rigor (FR-004, SC-001)
- **Metric**: Macro-F1 Score.
- **Baseline**: **Stratified Random Baseline**.
 - **Method**: Generate a baseline by shuffling labels **relative to the input features** while preserving the **marginal distribution** of each label (to maintain the multi-label correlation structure as a null baseline). This breaks the composition-label link while maintaining the label co-occurrence structure.
 - **Null Hypothesis**: "No relationship between composition and labels beyond label co-occurrence."
 - **Test**: **Permutation Test** (n=1,000 iterations).
 - **Success**: Model Macro-F1 > Baseline Macro-F1 by ≥ 0.05 AND p < 0.05.
- **Confusion Matrix**: Analyze error modes (e.g., pitting vs. SCC confusion).

### 5. Feature Importance & Sensitivity (FR-005, SC-003)
- **SHAP Analysis**: Calculate SHAP values to rank elemental contributions.
- **Reference Vector**:
 - **Construction**: A dedicated script (`literature_review.py`) will perform a systematic review of a specified set of review papers (Assumptions).
 - **Extraction Protocol**: Rule-based mapping: "Increases resistance" -> +1, "Decreases resistance" -> -1, "No effect" -> 0. Aggregate scores across papers, weighted by citation count or recency. Ensure independence from the training dataset's statistical correlations.
 - **Vectorization**: Convert to a quantitative vector (e.g., -1 to +1 scale).
 - **Validation**: Compare SHAP rankings vs. Reference Vector using **Spearman Rank Correlation (ρ)**.
 - **Success**: ρ ≥ 0.6.
 - **Constraint**: The 5 review papers used for the Reference Vector must *not* cover the specific alloy classes held out for the OOD test (if possible), or the OOD test is limited to generalization within the known classes.
- **Threshold Sensitivity**:
 - Sweep decision threshold: a central value ± a range of small magnitudes.
 - Report False Positive/Negative rate variance.
 - **Stability**: Metrics must remain within 5% variance.

### 6. Limitations & Assumptions (FR-006, FR-009)
- **Causal Framing**: All findings are explicitly framed as **associational**. No causal claims.
- **Environmental Variables**: If pH/temperature are missing (likely), apply a **Confounding Sensitivity Analysis**.
 - **Fallback**: If the sensitivity analysis cannot determine a specific factor, apply the **default 20% confidence interval widening factor** to satisfy FR-009.
 - **Annotation**: Output artifacts must include `[deferred]` annotation for the specific widening factor if the exact environmental context is unknown.
 - **Implementation**: `final_ci = calculated_ci * (1 + widening_factor)`.
