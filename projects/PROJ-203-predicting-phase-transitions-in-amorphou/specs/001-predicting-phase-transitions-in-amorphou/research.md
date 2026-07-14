# Research: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

## Dataset Strategy

The project relies on a hybrid data strategy: **Experimental Ground Truth** from verified external databases and **Synthetic Structural Descriptors** generated via MD simulation.

### 1. Experimental Thermal Properties (Ground Truth)
*Source*: The "Glass Transition Database (GTDB) v2.1" (Zenodo).
*Role*: Provides $T_g$ (Glass Transition) and $T_x$ (Crystallization) values to serve as labels.
*Constraint*: The project MUST NOT use simulation-derived thermodynamic signatures for labeling.

**Data Source Resolution**:
The `# Verified datasets` block provided in the prompt does **not** contain the specific URL for the GTDB.
- **Action**: The plan identifies the specific dataset: **Glass Transition Database (GTDB) v2.1**, Zenodo Record ID: `` (Placeholder for actual verified DOI).
- **Fallback**: If this URL is not provided or unreachable, the pipeline enters **"Pipeline Validation Mode"**. In this mode, the model is trained on *simulated* Tg values (from a separate, verified physics-based estimator) to test the *pipeline structure*, explicitly noting that this does not test the *hypothesis* of predicting experimental Tg. The RMSE target (≤15 K) is **not applicable** in this mode.

| Dataset Name | Verified URL | Format | Usage |
|:--- |:--- |:--- |:--- |
| Glass Transition Database (GTDB) v2.1 | *Pending Verification* | CSV/Tabular | Primary source for $T_g$, $T_x$. |
| NIST Chemistry WebBook | *No verified source in block* | JSON/CSV | Supplemental source for organic glass formers (if GTDB lacks). |

*Note*: The implementation will explicitly check for the presence of the GTDB URL. If missing, it will log a "Data Gap" alert and pause the research phase (Phase 1) until the URL is provided or the scope is reduced to Pipeline Validation.

### 2. Structural Descriptors (Synthetic)
*Source*: Generated via MD simulation using `LAMMPS` or `OpenMM`.
*Role*: Provides predictors (RDF peaks, bond angles, coordination numbers).
*Constraint*: Must be generated on CPU within 30 mins/composition.

**Dataset Strategy for Descriptors**:
- **Generation**: Run MD for a diverse set of compositions.
- **Cooling Rate**: Use high cooling rates typical for MD.
- **Assumption**: The plan relies on the **Cooling-Rate Invariance Assumption**: Short-range order descriptors (RDF peaks, coordination) are robust to cooling rate variations in the glassy state. This is supported by literature for many oxide/sulfide systems.
- **Filtering**: Exclude compositions known to be highly cooling-rate sensitive (e.g., certain organics) if literature suggests strong dependence.

| Dataset Name | Verified URL | Format | Usage |
|:--- |:--- |:--- |:--- |
| RDF Triple Summarization | https://huggingface.co/datasets/ttss/rdf-triple-based-summarization/resolve/main/train.csv | CSV | **NOT USED**. Irrelevant domain. |
| Medical RMSE | https://huggingface.co/datasets/arjunashok/medical-5day-zeroshot-freshexps-test-plot_with_rmsesort/resolve/main/data/test-00000-of-00001.parquet | Parquet | **NOT USED**. Irrelevant domain. |
| NIST 800-53 | https://huggingface.co/datasets/rkreddyp/nist_800_53/resolve/main/nist.jsonl | JSONL | **NOT USED**. Security compliance, not chemistry. |
| WebBooks-1 | https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt | Text | **NOT USED**. Book corpus, not chemical properties. |

**Critical Finding**: The provided `# Verified datasets` block **does not contain any dataset relevant to amorphous solids, MD simulations, or thermal properties**.
**Plan Adjustment**: The project will **not** use any of the verified URLs in the block as they are domain-mismatched. Instead, the pipeline will:
1. **Generate** structural descriptors locally via MD simulation (no external dataset needed for this step, only force fields).
2. **Fetch** experimental labels from GTDB (if URL provided) or flag as 'missing'.
3. **Flag** this as a "Data Source Gap" in the final report if GTDB is unavailable.

## Methodology

### 1. Data Generation Pipeline (FR-001, FR-008)
- **Simulation**: Use `LAMMPS` (via `pylammps` or script execution) to relax a representative set of compositions.
- **Cooling Rate**: Use standard MD rates. **No time-scaling** to experimental rates (physically impossible).
- **Descriptor Extraction**:
 - RDF: Calculate $g(r)$, extract peak position ($r_{peak}$) and width ($\sigma$).
 - Bond Angles: Calculate variance and skewness of angle distributions.
 - Coordination: Count neighbors within first coordination shell.
- **Truncation**: If simulation > 30 mins, truncate to last 500 steps (Constitution Principle VII).
- **Relaxation Check**: Verify energy convergence in the final 500 steps. If energy is still drifting, flag as 'non-relaxed' and exclude from training.

### 2. Labeling (FR-002)
- **Crystallization Propensity**: $Label = 1$ if $T_x - T_g \le 50$ K, else $0$.
- **Source**: Experimental $T_g, T_x$ from GTDB (if available).
- **Threshold Justification**: The 50K cutoff is a heuristic proxy for "low stability" based on literature ranges for glass fragility. It is not a universal physical constant.

### 3. Modeling (FR-003)
- **Algorithm**: Random Forest Regressor (sklearn) and Classifier.
- **Constraints**: CPU-only, max 6h runtime.
- **Validation**: 5-fold Cross-Validation.
- **Metrics**: RMSE (Regression), ROC-AUC (Classification).
- **Power Analysis**: For N=500, the detectable effect size is moderate. If the model fails to achieve RMSE ≤ 15 K, the plan will trigger a "Sample Size Expansion" (Phase 0: run 500 more compositions) or report the achieved RMSE with a power-limitation statement.

### 4. Interpretability (FR-004, FR-005)
- **SHAP**: Compute SHAP values for feature ranking.
- **Family Stratification**: Compare feature importance across Oxide, Sulfide, Organic.
- **Correction**: Apply Bonferroni correction for multiple comparisons across families.

### 5. Sensitivity Analysis (FR-006, SC-004)
- **Range**: Vary crystallization threshold: **25 K, 50 K, 75 K**.
- **Output**: Report FPR, Class Balance, and Accuracy for each cutoff.
- **Purpose**: Measure model robustness to the heuristic threshold, not to validate the threshold itself.

### 6. Collinearity Diagnostics (FR-007)
- **Method**: Calculate Variance Inflation Factor (VIF) for all predictors.
- **Output**: `docs/reports/collinearity_report.json`.
- **Action**: If VIF > 5, report collinearity and consider feature removal (if justified).

## Power / Sample-Size Note

For N=500 samples across 3 families, the power to detect small non-linear effects is limited. The plan includes a **Sample Size Expansion Contingency**:
- If the initial model (N=500) fails the RMSE target (≤15 K) or shows high variance, the pipeline will automatically trigger a secondary simulation batch (Phase 0) to reach N=1000.
- If expansion is not feasible, the success criteria will be adjusted to report the achieved RMSE with a power-limitation statement.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Experimental Data** | High | The `# Verified datasets` block lacks thermal property sources. Plan to use GTDB (if URL provided) or fall back to 'Pipeline Validation Mode' (simulated labels). |
| **MD Simulation Timeout** | High | 500 comps * 30m > 6h limit. Strict timeout per comp; truncate to final 500 steps. Exclude non-relaxed states. |
| **Collinearity** | Medium | Compositional features may correlate with structural ones. Calculate VIF; report collinearity diagnostics (FR-007). |
| **Overfitting** | Medium | Small dataset (500 rows). Use 5-fold CV; limit tree depth; report power limitations if RMSE > 15 K. |
| **Cooling Rate Mismatch** | High | MD rates (extreme heating rates) vs Experimental (moderate heating rates). Rely on Cooling-Rate Invariance Assumption. Filter sensitive compositions. |

## Decision Rationale

- **Random Forest over Deep Learning**: The limited CPU time and RAM constraint make deep learning infeasible. RF is robust, interpretable (via SHAP), and CPU-native.
- **Truncation Strategy**: Essential to meet the 6h CI limit. Truncating to final 500 steps captures the relaxed state without incurring the full simulation cost.
- **No External Dataset for Descriptors**: Structural descriptors must be generated from the specific compositions of interest; pre-existing RDF datasets (like the NLP ones in the verified block) are irrelevant.
- **Two-Stage Pipeline**: Separating simulation (Phase 0) from training (Phase 1) is the only way to satisfy the 6h CI limit while maintaining the scientific hypothesis.