# Research: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## 1. Problem Definition & Scientific Rationale

### 1.1 Research Question
How do compositional descriptors (beyond rule-of-mixtures) predict the **Residual Bulk Modulus** ($B_{observed} - B_{Miedema}$) in High-Entropy Alloys (HEAs)?

### 1.2 Rationale
HEAs exhibit complex non-linear interactions between constituent elements that simple rule-of-mixtures (e.g., Miedema's model) cannot fully capture. By modeling the *residual* (the deviation from the Miedema prediction), we isolate the specific "alloying effect" driven by local lattice distortion, entropy, and electronic effects. The use of **Isometric Log-Ratio (ILR)** transformation is critical to handle the compositional nature of the data (sum-to-one constraint), preventing singular matrices in regression and enabling valid statistical inference.

## 2. Dataset Strategy

### 2.1 Primary Source: Materials Project & OQMD APIs
The study requires atomic compositions and elastic constants ($C_{ij}$) for alloys with $\ge 5$ principal elements.
* **Source**: Materials Project API and Open Quantum Materials Database (OQMD).
* **Verification Status**: The "Verified datasets" block provided for this project **does not contain a verified URL** for raw HEA elastic constant data from these specific APIs.
* **Strategy**:
 1. The pipeline will attempt to fetch data directly from the official Materials Project and OQMD public APIs (as per Constitution Principle VI).
 2. If API access is blocked or fails, the pipeline will attempt to load the generic OQMD targets CSV from the verified HuggingFace source: `.
 3. **Literature Merge**: If the API and generic CSV yield $< 500$ samples, the pipeline will attempt to merge with verified HEA elastic datasets from literature (e.g., specific HEA elastic constants databases cited in [Reference: HEA Elastic Constants Database, 2023]).
 4. **Constraint**: If the merged dataset still lacks the specific HEA subset ($\ge 5$ elements + elastic constants) or total count $< 500$, the pipeline will halt with a "Dataset Insufficient" error (SC-001) rather than proceeding with an invalid dataset.
 5. **No Fabrication**: No other dataset URLs will be invented or substituted.

### 2.2 Dataset Strategy Table

| Dataset Name | Source URL (Verified) | Loader Method | Status |
|:--- |:--- |:--- |:--- |
| **OQMD Targets** | ` | `pandas.read_csv()` | Fallback only (if API fails) |
| **HEA Elastic Data** | *No verified URL in block* | `requests` (API) | Primary Source (API) |
| **ILR Reference** | ` | N/A | *Not used for data* (Reference only) |

> **Critical Note on Dataset Fit**: The spec requires specific HEA elastic data. The verified OQMD CSV (`kjappelbaum/chemnlp-oqmd`) is a generic targets file and may not contain the specific HEA subset with $\ge 5$ elements required by FR-001. The plan explicitly handles this by checking sample counts ($\ge 500$) and attempting a literature merge, halting only if the dataset is insufficient.

## 3. Methodology

### 3.1 Data Ingestion & Preprocessing
1. **Retrieval**: Fetch HEA entries with $\ge 5$ elements and reported elastic constants ($C_{11}, C_{12}, C_{44}$).
2. **Normalization**: Ensure atomic percentages sum to 1.0. Log adjustments if they do not.
3. **Descriptor Calculation**:
 * Compute mixing enthalpy (Miedema), atomic radius variance, electronegativity variance, etc.
 * **Exclusion Rule**: If the target is **Residual Bulk Modulus**, **exclude** any Miedema-derived features from the predictor set (FR-008) to prevent circular validation.
4. **ILR Transformation**: Apply Isometric Log-Ratio transformation to the composition vector to break the closure constraint (FR-003).

### 3.2 Target Variable & Residual Validation
* **Target**: $Y = B_{observed} - B_{Miedema}$.
* **Validation Logic**: The system will calculate the Pearson correlation ($|r|$) between the residuals ($Y$) and the compositional descriptors (e.g., radius variance, electronegativity variance).
 * **Scientific Interpretation**: A correlation $|r| \ge 0.1$ is **expected and desirable**. It indicates that the chosen descriptors are successfully capturing the non-linear alloying effects (lattice distortion, electronic structure changes) that Miedema's rule-of-mixtures model failed to predict. This correlation is the **primary signal** the model is designed to learn.
 * **System Action**: If $|r| \ge 0.1$, the system logs a **diagnostic success message**: "Descriptors successfully capture alloying effects (|r| = [value])". This confirms the physical validity of the descriptor set.
 * **Low Correlation Case**: If $|r| < 0.1$, the system logs a note: "Residual signal weak; descriptors may not capture dominant alloying effects or noise dominates." This prompts a review of descriptor selection or data quality.
 * **No Confound**: This correlation is **not** treated as a confound or error. It is the evidence that the residual target is meaningful and the descriptors are relevant.

### 3.3 Modeling Strategy
* **Algorithms**: Random Forest (RF), Gradient Boosting (GB), ElasticNet (EN).
* **Infrastructure**: CPU-only (scikit-learn default). No GPU.
* **Validation**:
 * Split: [deferred] Train, [deferred] Validation, [deferred] Test.
 * **Grouped Bootstrap**: 1000 iterations, grouping by **composition_string** (exact elemental ratios, e.g., "CrMnFeCoNi_50-50") to prevent data leakage from stoichiometric variations.
 * **Fallback Logic**: If the number of unique composition groups is $< 10$, the system logs a warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution" and proceeds, rather than halting, to allow for diagnostic reporting.
 * **Multiple Comparison Correction**: Apply False Discovery Rate (FDR) correction to p-values from pairwise model performance comparisons.
* **Hyperparameter Tuning**: Grid search with 5-fold CV (within the training set).

### 3.4 Statistical Rigor & Sensitivity
* **Null Hypothesis**: $R^2 = 0$. Test significance ($p < 0.05$).
* **Sensitivity Analysis**: Sweep $R^2$ null thresholds $\{0.25, 0.30, 0.35\}$.
 * Estimate Type I error rate via **permutation testing** at each threshold.
 * **Permutation Strategy**: The null distribution is generated by shuffling the target variable ($Y$) relative to the predictors ($X$), preserving the predictor structure. This ensures a valid estimate of the false-positive rate under the null hypothesis of no relationship.
 * Report variance in false-positive rates (FR-006).
* **Sample Size**: Hard halt if $< 500$ samples after all fallback merges (SC-001).

### 3.5 Interpretability & Reporting
* **SHAP/Permutation**: Identify top 3-5 descriptors.
* **Associational Framing**: Final report MUST include: "These findings are associational and do not imply causation" (FR-007, SC-004).
* **Visuals**: Parity plots, Partial Dependence Plots (PDP).

## 4. Compute Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Memory Management**:
 * Data subset to fit $\le 7$ GB RAM.
 * Use `float32` for all arrays.
 * Avoid loading full OQMD if possible; filter by HEA criteria during fetch.
* **Runtime**:
 * Target: $< 6$ hours.
 * If training exceeds time limits, reduce grid search size or use early stopping.
* **No GPU**: All models are CPU-tractable (RF, GB, EN). No deep learning.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use ILR Transformation** | Required to handle compositional singularity (FR-003). |
| **Residual Target ($B_{obs} - B_{Miedema}$)** | Isolates alloying effects; requires exclusion of Miedema features (FR-008). |
| **Grouped Bootstrap (by composition_string)** | Prevents leakage from similar chemical spaces and stoichiometric variations (FR-005). |
| **Fallback to Standard Bootstrap** | Ensures pipeline completion if groups < 10, with caution flag. |
| **Hard Halt on < 500 samples** | Ensures statistical power; prevents underpowered models (SC-001). |
| **No Miedema Features for Residual Target** | Prevents circular validation and multicollinearity (FR-008). |
| **FDR Correction** | Controls false positives in multiple model comparisons (FR-005). |
| **Literature Merge Fallback** | Ensures sample size feasibility if APIs are insufficient. |
| **Residual Correlation as Success Signal** | Correlation between residuals and descriptors indicates the descriptors capture the non-linear alloying effects Miedema missed; this is the intended physical signal, not a confound. |