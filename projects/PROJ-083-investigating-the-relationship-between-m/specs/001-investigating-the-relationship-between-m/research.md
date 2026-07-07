# Research: Molecular Topology and Reaction Selectivity

## 1. Dataset Strategy

The project relies on the **USPTO-50k** dataset for reaction data. Per the "Verified datasets" block, the following sources are available:

| Dataset Name | Type | Verified URL(s) | Usage |
|:--- |:--- |:--- |:--- |
| USPTO-50k | JSONL/Parquet | `<br>`<br>` | Primary source for reaction SMILES (reactants/products). |
| ReactionRecord | N/A | NO verified source found | Internal data structure; not an external dataset. |

**Selection Rationale**: The USPTO-50k dataset is the standard benchmark for reaction prediction and contains the necessary SMILES strings to parse reactants and products. The `parquet` version from `pingzhili` is preferred for efficient loading, with `jsonl` as a fallback.

**Variable Fit Verification**:
- **Predictors**: Topological indices (Wiener, Balaban, Zagreb) derived from *reactant* SMILES.
- **Target**: **Theoretical Regioisomer Count** derived from *reactant* symmetry (number of non-equivalent substitution sites).
- **Constraint**: The dataset must contain reactant SMILES. The USPTO-50k sources listed above are known to contain reactant fields.
- **Gap Check**: The dataset does NOT contain observed regioisomer diversity counts (it is a single-product dataset). The target is therefore *computed* as the number of symmetry-unique substitution sites on the reactant ring. If the reactant is symmetric (e.g., benzene), the count is 1. This approach is chemically valid and avoids the infeasible derivation from product SMILES.
- **Note**: The "default to 0" logic in the spec is incorrect. The count is **always** derived from symmetry (e.g., benzene = 1, toluene = 3). There is no "missing data" scenario for the target; it is a computed property of the reactant.

## 2. Topological Descriptor Strategy

**Method**: Use `rdkit` to compute graph-based descriptors.
- **Wiener Index**: Sum of all shortest path distances in the unweighted molecular graph.
- **Balaban Index**: Based on the distance matrix and graph connectivity.
- **Zagreb Index**: Sum of squared vertex degrees.

**Validation Plan**:
- Benchmark against known values: Benzene (Wiener=27), Toluene (Wiener=33), Nitrobenzene (Wiener=45).
- Tolerance: ±0.1.
- **Handling Failures**: If a molecule has disconnected components or invalid valence, flag as "invalid topology" and exclude from regression (per FR-002).

## 3. Statistical Modeling Strategy

**Primary Models**:
1. **Ordinal Logistic Regression**: To model the deterministic integer count (1, 2, 3) as an ordered categorical variable. This is the scientifically appropriate model for symmetry-derived counts.
2. **Random Forest Regression**: To capture non-linear relationships and serve as a robustness check.
3. **Poisson Regression**: **Excluded as primary model**. It assumes a stochastic process which contradicts the deterministic nature of the target. It may be run only as a baseline to demonstrate the unsuitability of stochastic models, but results will not be reported as valid findings.

**Validation & Cross-Validation**:
- **Standard**: 5-fold Cross-Validation.
- **Small N (<20)**: Switch to Leave-One-Out (LOO) CV (per FR-005).
- **Degenerate Target (Variance=0)**: If the target is constant (e.g., all reactants are benzene), the system MUST halt with "Insufficient Variance" (per FR-007). No fallback to ZIP or Binary Classification is used, as the target is deterministic. The output will be a descriptive report of the constant target.

**Metrics**:
- **Ordinal Regression**: Pseudo-R², RMSE, Accuracy (predicted class).
- **Random Forest**: R², RMSE.
- **Baseline (Poisson)**: R², RMSE (expected to be low; not used for inference).

**Statistical Rigor**:
- **Multiplicity**: Bonferroni correction applied for 3 tests (alpha = 0.0167).
- **Collinearity**: Variance Inflation Factor (VIF) calculated. If VIF > 5, indices analyzed sequentially.
- **Causality**: Claims framed as **associational** only (observational data).
- **Confounding Variables**: The analysis explicitly acknowledges that reaction conditions (catalyst, temperature, solvent) are omitted variables. These may confound the relationship between topology and selectivity. The study does not claim causality. A sensitivity analysis will be performed by stratifying reactions by electrophile type if metadata permits.

**Power Analysis**:
- **Minimum Detectable Effect (MDE)**: The plan mandates reporting the MDE for the observed variance in the target. Given the target is a small integer (1-3), the power to detect small effect sizes is limited.
- **Low Variance Scenario**: If the target variance is low (e.g., >90% of samples have count=1), the power to detect a significant correlation may be near zero. In such cases, the primary output will be a **descriptive analysis** of the target distribution rather than a regression model. The paper will explicitly state this power limitation.

## 4. Compute Feasibility

- **Environment**: GitHub Actions Free Tier (standard CPU allocation, sufficient RAM).
- **Strategy**:
 - Use `scikit-learn` and `statsmodels` (CPU optimized).
 - No GPU/CUDA usage.
 - Data subset to a constrained RAM limit.
 - Descriptor calculation capped at 15 minutes (per SC-003).
- **Risk Mitigation**: If descriptor calculation exceeds 15 mins, pipeline logs warning and proceeds with available data or switches to a sampled subset.

## 5. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **USPTO-50k (Parquet)** | Efficient loading on CPU; verified source available. |
| **Ordinal Regression** | Target is deterministic integer count; Ordinal regression is scientifically valid. |
| **Halt on Variance=0** | Target is deterministic; no stochastic fallback (ZIP) is appropriate. |
| **CPU-Only** | Mandatory for CI compatibility; no GPU available. |
| **Reactant-Derived Target** | Avoids tautology; tests correlation between topology and symmetry. |
| **Tautology Acknowledgement** | Predictors and target derive from the same graph; analysis tests if global indices are sufficient proxies for local symmetry. |
| **Spec Revision Required (Synthetic Test)** | The spec's synthetic test (Poisson generation) is scientifically invalid for a deterministic target. It must be updated to a deterministic symmetry-based generator. |
| **Spec Revision Required (Poisson FR)** | The spec's requirement for Poisson Regression (FR-004) is invalid. It must be replaced with Ordinal Regression. |

## 6. Spec Revision Required (Summary)

The following elements in the source `spec.md` are scientifically invalid and must be updated:

1. **FR-004 & FR-007**: Replace "Poisson Regression" and "Zero-Inflated Poisson" with "Ordinal Logistic Regression" and "Descriptive Statistics/Binary Classification" (if variance=0).
2. **User Story 3 (Independent Test)**: Replace the synthetic test `target ~ Poisson(exp(Xβ))` with a deterministic symmetry-based generation (e.g., `target = f(symmetry_class)`).
3. **Assumptions (Dataset Variable Fit)**: Remove the "default to 0" logic. The target is always derived from reactant symmetry (e.g., benzene = 1).