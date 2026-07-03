# Research: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Executive Summary

This research investigates the **structural correlation** between topological features of reactant molecules (Wiener, Balaban, Zagreb indices) and the **theoretical** regioisomer diversity of Electrophilic Aromatic Substitution (EAS) reactions. 

**Critical Methodological Clarification**: The USPTO-50k dataset does not contain lists of all possible regioisomers. It typically lists a single major product. Therefore, the "Regioisomer Diversity Count" cannot be derived by counting dataset entries (which would yield ~1 for almost all records). Instead, the target is derived via **reaction template enumeration** on the *reactant* graph. 

**Reframed Scientific Goal**: Since the target is a deterministic function of the reactant graph, the predictors (topological indices) are definitionally correlated with the target. The analysis is **not** a predictive model of an independent outcome. It is a **Structural Correlation & Graph Complexity Study**. The goal is to:
1.  Quantify the *degree* of definitional correlation (how well graph complexity metrics map to substitution site counts).
2.  Identify *non-linearities* or *deviations* from the theoretical 1:1 complexity-to-site relationship (e.g., steric hindrance effects captured by Balaban index that reduce effective diversity).
3.  Validate the robustness of topological indices as proxies for theoretical reactivity patterns.

All claims are framed as **associational/structural correlations**. No causal claims are made.

## Dataset Strategy

### Primary Dataset: USPTO-50k
- **Source**: HuggingFace Datasets.
- **Verified URLs**:
  - `https://huggingface.co/datasets/pingzhili/uspto-50k/resolve/main/data/train-00000-of-00001.parquet`
  - `https://huggingface.co/datasets/Congliu/USPTO-50k-Instruction/resolve/main/uspto_test.json`
  - `https://huggingface.co/datasets/scaliaven/uspto-50k/resolve/main/forward_synthesis.jsonl`
- **Rationale**: This is the standard benchmark for reaction prediction. It contains reactant/product SMILES and reaction conditions.
- **Variable Fit**:
  - **Reactant SMILES**: Available. Used for topological descriptors and target enumeration.
  - **Reaction Type**: **NOT** explicitly labeled in standard splits. Must be inferred via SMARTS pattern matching (see Methodology).
- **Constraint**: The dataset is observational. No randomization of reactants exists.
- **Target Variable Limitation**: The dataset typically lists only the *major* product SMILES. It does not provide a list of all possible regioisomers. Therefore, the "Regioisomer Diversity Count" cannot be derived by counting existing entries (which would yield ~1 for almost all records). Instead, we derive the *theoretical* count via enumeration.

### Dataset Variable Verification
- **Required**: Reactant SMILES, Reaction Type (inferred).
- **Verified**: The USPTO-50k dataset contains reactant SMILES. Reaction type must be inferred.
- **Missing Data Handling**: If a reaction lacks valid SMILES, it is excluded (FR-006). If EAS filtering yields < 100 reactions, the pipeline halts (US-1).

## Methodology

### 1. Data Ingestion & Filtering (FR-001, FR-006)
- **Download**: Fetch the primary Parquet file from the verified HuggingFace URL.
- **Parsing**: Use `pandas` to load the Parquet file.
- **EAS Filtering**:
  - **SMARTS Patterns**: Identify EAS reactions using specific SMARTS patterns for electrophilic aromatic substitution.
    - **Pattern 1 (Aromatic Ring)**: `[c:1]1[cH][cH][cH][cH][cH]1` (Benzene-like) or `[c:1]1[cH][cH][cH][cH][cH]1` with substituents.
    - **Pattern 2 (Electrophile Attachment)**: Detect the formation of a bond between an aromatic carbon and an electrophile (e.g., `[c:1][N+](=O)[O-]` for nitration, `[c:1][Br]` for bromination, `[c:1][S+]` for sulfonation).
    - **Combined Logic**: A reaction is EAS if the reactant contains an aromatic ring and the product shows a new bond to an electrophile on that ring, without breaking the aromaticity of the ring.
  - **Validation**:
    - **Cross-Reference**: Where available, cross-reference with the USPTO-50k reaction class taxonomy (if the specific split includes class labels).
    - **Manual Spot-Check**: Randomly sample 100 filtered reactions and manually verify against the reaction type (EAS vs. others) to ensure high precision (>95%).
  - **High-Precision Heuristic**: Use a combination of aromatic ring presence and specific electrophile patterns to ensure purity.
- **Error Handling**: Log malformed SMILES and exclude them without crashing.

### 2. Target Variable Definition (FR-003)
- **Definition**: "Theoretical Regioisomer Count" = Number of distinct regioisomeric products that *can* be formed from the reactant via the EAS mechanism.
- **Derivation**:
  - **Step 1: Sanitization**: Before enumeration, sanitize the reactant SMILES using `rdkit.MolFromSmiles` with `sanitize=True`. Remove salts (disconnects), explicit hydrogens, and normalize valence. If sanitization fails, exclude the record.
  - **Step 2: Enumeration**: Apply a generic EAS reaction template (e.g., `[c:1][*]>>[c:1][E]` where E is a generic electrophile) to all aromatic carbons in the sanitized reactant.
  - **Step 3: Counting**: Count the number of distinct canonical SMILES generated.
  - **Fallback**: If enumeration fails (e.g., graph ambiguity, disconnected components) or returns 0, **exclude the record** (do not default to 1) to prevent noise. This ensures the target variable is based on valid theoretical derivations only.
- **Rationale**: The USPTO-50k dataset typically lists only the major product, making direct counting impossible. Enumeration ensures the target variable has variance and reflects the theoretical selectivity of the reactant.
- **Dependency Note**: The target is derived from the *reactant* graph, meaning it is definitionally correlated with the topological descriptors. The analysis will focus on the *strength* of this correlation and deviations from linearity, rather than assuming independence.

### 3. Topological Descriptor Calculation (FR-002)
- **Tools**: `rdkit` (CPU-only).
- **Descriptors**:
  - **Wiener Index**: Sum of all shortest path distances between pairs of atoms.
  - **Balaban Index**: Based on the number of cycles and distances.
  - **Zagreb Index**: Sum of squared degrees of vertices.
- **Validation**:
  - Test on **benzene** (Expected Wiener: 5), **toluene** (Expected: 9), **nitrobenzene** (Expected: 13).
  - Flag molecules with disconnected graphs or invalid valence.
- **Performance**: Target < 15 minutes for the full filtered set.

### 4. Statistical Modeling (FR-003, FR-004, FR-005)
- **Distribution Check**: Before modeling, validate the target distribution.
  - **Degenerate Case**: If variance is near zero (e.g., all counts = 1), switch to **Binary Diversity** classification (Count > 1 vs. 1) or **Ordinal Regression**.
  - **Zero-Inflated**: If the distribution is heavily zero-inflated (unlikely for theoretical count, but possible if enumeration fails for many), switch to **Zero-Inflated Poisson (ZIP)**.
- **Models**:
  1.  **Poisson Regression**: Baseline for count data.
  2.  **Zero-Inflated Poisson (ZIP)**: Contingency plan if the data is zero-inflated or degenerate.
  3.  **Random Forest Regression**: Non-linear, robust to outliers. Used to capture non-linearities in the structural correlation.
- **Validation Strategy**:
  - **5-Fold Cross-Validation**: Default.
  - **LOO Cross-Validation**: If N < 20 (FR-005).
- **Metrics**:
  - **R²** (Pseudo-R² for Poisson/ZIP).
  - **RMSE**.
  - **Deviation from Linearity**: Measure how much the model deviates from a perfect 1:1 correlation (theoretical expectation).
- **Significance Testing**:
  - Test correlation of each index with the target.
  - **Multiplicity Correction**: Bonferroni correction (α = 0.05/3 ≈ 0.0167).
  - **Collinearity**: Calculate Variance Inflation Factor (VIF). If VIF > 5, analyze indices sequentially or jointly.
- **Causal Framing**: All results are **associational/structural correlations**. No causal claims.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni correction applied to the three primary indices.
- **Power**: Assuming N > 1000 after EAS filtering, power is likely sufficient. If N < 20, LOO is used.
- **Measurement Validity**: Indices are standard (Wiener, Balaban 1982).
- **Collinearity**: VIF diagnostics will be reported. If high, the model interpretation will be adjusted.
- **Dataset Fit**: Confirmed that USPTO-50k contains necessary SMILES fields. Target derived via enumeration to ensure variance.
- **Target Dependency**: Acknowledged that the target is derived from the reactant graph, creating a definitional correlation. The study investigates the nature of this structural correlation and deviations from theoretical expectations.

## Decision Rationale (Compute Feasibility)

- **Why CPU-only?**: The GitHub Actions free tier has no GPU. `rdkit`, `scikit-learn`, and `statsmodels` are highly optimized for CPU.
- **Why Poisson/ZIP?**: The target is a count variable. ZIP handles potential zero-inflation or degeneracy.
- **Why Random Forest?**: To capture non-linear relationships without assuming a specific functional form.
- **Why LOO fallback?**: Ensures validation is always possible, even with small subsets.

## Ethical & Safety Considerations

- **Data Privacy**: USPTO-50k is public chemical data. No PII.
- **Bias**: The dataset may be biased towards common reactions. Findings may not generalize to rare chemistries.
