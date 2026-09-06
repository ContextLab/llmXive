# Project Specification: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

## Version History

- **v1.0 (Initial Draft)**: Focused on Yield Strength and Elongation as primary targets.
- **v1.1 (Pivot to DFT Proxies)**: Updated to target **Bulk and Shear Moduli** as surrogates for mechanical properties to leverage high-throughput DFT databases (OQMD).
- **v1.2 (Refined Constraints & Clustering)**: Explicitly defined **Bulk and Shear Moduli** as the sole optimization targets. Updated Success Criteria to include K-Means clustering for decoupling analysis and Rule of Mixtures bounds.
- **v1.3 (Convergence Revision)**: Resolved contradictions between SC-003 and Constitution Principle VII; added statistical validation (permutation test) to SC-002; mandated isometric log-ratio (ilr) transform in FR-005; defined sensitivity analysis artifacts in FR-006; clarified stop conditions and uncertainty metrics in User Stories.
- **v1.4 (Physics & Traceability Revision)**: Added FR-000 for physical feasibility check; redefined 'System' for LOSO-CV to prevent elemental leakage; clarified 'decoupling' as deviation from Poisson's ratio; added explicit traceability anchors to all FRs/SCs; defined all ambiguous metrics (hull radius, robustness_score, uncertainty_variance).

## 1. Executive Summary

This project aims to identify alloy compositions that optimize the trade-off between **Bulk Modulus** (resistance to uniform compression) and **Shear Modulus** (resistance to shear deformation). Unlike previous iterations focusing on yield strength, we utilize **Bulk and Shear Moduli** as DFT-derived proxies to access larger, high-quality public datasets (OQMD). 

**Critical Physics Note**: Bulk (K) and Shear (G) moduli are physically coupled via Poisson's ratio (ν) by the relationship $G = 3K(1-2\nu)/2(1+\nu)$. In most metallic systems, this enforces a strong positive correlation. This project redefines "decoupling" as either (a) a statistically significant deviation from the global correlation trend (if correlation < 0.95) or (b) a significant deviation from the theoretical Poisson's ratio line (if global correlation > 0.95), ensuring the research question remains answerable.

## 2. Functional Requirements

### FR-000: Physical Feasibility Check
The system MUST perform a preliminary check on the global correlation between Bulk and Shear Moduli in the ingested dataset.
- If the global Pearson correlation coefficient $r < 0.95$, the system proceeds with standard "decoupling" analysis (low correlation clusters).
- If the global Pearson correlation coefficient $r \ge 0.95$, the system MUST pivot to a "Poisson's Ratio Anomaly" analysis, where "decoupled" is defined as points with residuals from the theoretical $G(K)$ line exceeding a threshold of 0.1 GPa.
- This check MUST be logged in `data/processed/feasibility_report.json` with the field `global_correlation` and `analysis_mode` (either "standard" or "poisson_anomaly").

### FR-001: Data Ingestion
The system must ingest compositional data and corresponding **Bulk and Shear Moduli** values from the OQMD dataset via HuggingFace. It must filter for entries where both moduli are positive and non-null.

### FR-001.1: Data Sufficiency
The system MUST verify that the filtered dataset contains at least **500 valid entries**. If valid entries < 500, the system MUST exit with error code 1 and log a critical error stating "Insufficient data for research validity; minimum 500 entries required." This requirement directly supports US-1 Acceptance Criteria 4.

### FR-002: Composition Encoding
The system must encode alloy compositions into feature vectors using elemental fractions and periodic descriptors (atomic radius, electronegativity) for every element present in the composition. The encoding MUST apply an isometric log-ratio (ilr) transform to the elemental fractions before any clustering or distance-based calculations.

### FR-003: Surrogate Modeling
The system must train separate Gradient Boosting Regressors to predict **Bulk Modulus** and **Shear Modulus** from the encoded composition features. 
- **Validation Strategy**: The system MUST use **Leave-One-System-Out Cross-Validation (LOSO-CV)**.
- **Definition of "System"**: For the purpose of LOSO-CV, a "System" is defined as a **Chemical System Group** (e.g., all alloys where Iron is the primary constituent vs. all alloys where Nickel is the primary constituent) to ensure no shared elemental descriptors exist between the training and test sets, preventing elemental interpolation leakage.
- Models must be validated using this strict LOSO-CV strategy to ensure true out-of-distribution generalization.

### FR-004: Pareto Optimization
The system must generate a Pareto frontier of optimal **Bulk and Shear Moduli** combinations using a genetic algorithm (NSGA-II) over a synthetic compositional space constrained strictly within the convex hull of the training data. 
- **Hull Definition**: The "convex hull" is defined as the convex hull of the training data points in ilr-transformed space.
- **Uncertainty Flagging**: The system MUST calculate prediction uncertainty via cross-validation variance and flag any points approaching the hull boundary (distance < 5% of hull radius) in the output.
- **Hull Radius Definition**: "Hull radius" is defined as the maximum Euclidean distance from the centroid of the training data in ilr-space to any training point.
- **Artifact Generation**: The system MUST output `data/processed/model_validation_report.json` containing a field `uncertainty_variance` for each point. `uncertainty_variance` is defined as the variance of the predicted Bulk/Shear Moduli across the 5-fold LOSO-CV splits for that specific composition.

### FR-005: Decoupling Analysis
The system must perform K-Means clustering on the compositional space (ilr-transformed) to identify regions where **Bulk and Shear Moduli** exhibit low correlation (decoupled regions) OR high deviation from the Poisson line (if FR-000 triggers). 
- **Traceability**: This requirement supports **US-3** and **SC-002**.
- **Method**: K-Means clusters based on distance in feature space. The "decoupled" label is assigned post-hoc to clusters meeting the criteria in SC-002.
- **Output**: The system MUST identify at least one cluster meeting the "decoupled" criteria defined in SC-002.

### FR-006: Sensitivity Analysis
The system must perform a sensitivity analysis on the **correlation threshold** (or residual threshold if in Poisson mode) used to define "decoupled" regions. 
- **Traceability**: This requirement supports **US-3**.
- **Sweep Range**: The system MUST sweep the threshold across a high-probability range in discrete steps.
- **Robustness Score**: The system MUST calculate a `robustness_score` for each threshold. `robustness_score` is defined as the **Jaccard Index** of cluster membership between the current threshold and the threshold ±0.1 steps.
- **Output**: The system MUST output a CSV file `data/processed/sensitivity_analysis.csv` containing a `robustness_score` for each threshold.

## 3. Success Criteria

### SC-001: Model Performance
The surrogate models for **Bulk and Shear Moduli** must achieve an R² score > 0.6 on the LOSO-CV test sets (using the "Chemical System Group" definition of System).

### SC-002: Decoupling Identification
The system must identify at least one compositional cluster where the correlation coefficient between **Bulk and Shear Moduli** is significantly lower than the global correlation (if global r < 0.95) OR the residual variance from the theoretical Poisson line is significantly high (if global r ≥ 0.95).
- **Traceability**: This criterion supports **US-3**.
- **Statistical Definition**: "Significantly lower" is defined as a delta > 0.2 verified by a permutation test (1000 iterations, p < 0.05). The permutation test MUST generate a null distribution by shuffling the *global* dataset labels and re-clustering, not just shuffling within the cluster.
- **Threshold Definition**: If global r < 0.95, the target cluster must have correlation < 0.5. If global r ≥ 0.95, the target cluster must have residual variance > 0.1 GPa.

### SC-003: Pareto Frontier Quality
The generated Pareto frontier must contain non-dominated points that maximize coverage within and extend to the boundary of the empirical convex hull of the training data, respecting **DFT-derived physical bounds (Rule of Mixtures for Bulk/Shear)**.
- **Coverage Definition**: "Maximize coverage" is defined as maximizing the area of the convex hull of the Pareto frontier points relative to the theoretical convex hull of the training data.
- **Boundary Definition**: Points are allowed "within or on the boundary" of the convex hull. The 5% margin is used only for uncertainty flagging (FR-004), not for point exclusion.

## 4. User Stories

### US-1: Data Extraction and Composition Encoding
**As a** materials scientist,
**I want** to ingest public alloy data filtered for **Bulk and Shear Moduli**,
**So that** I can encode compositions and prepare a clean dataset for modeling.

**Acceptance Criteria:**
1. The system loads data from `OQMD/elastic_properties` and filters for valid **Bulk and Shear Moduli**.
2. The output CSV (`data/processed/encoded_alloys.csv`) contains no nulls in key columns.
3. Feature vectors include at least two periodic descriptors per element.
4. If valid entries < 500, the system MUST exit with error code 1 and log a critical error stating "Insufficient data for research validity; minimum 500 entries required." (Supported by FR-001.1).
5. **Flow Control**: If this step exits due to insufficient data, the process terminates immediately; subsequent steps (US-2, US-3) are skipped.

### US-2: Surrogate Model Training and Pareto Generation
**As a** researcher,
**I want** to train models on **Bulk and Shear Moduli** and generate a Pareto frontier,
**So that** I can visualize the trade-offs and identify optimal regions.

**Acceptance Criteria:**
1. Models achieve R² > 0.6 on LOSO-CV (using Chemical System Group definition).
2. A Pareto frontier is generated using NSGA-II with a fixed time budget.
3. Synthetic points are clamped to physical limits (moduli > 0) and strictly within the convex hull (or on the boundary).
4. Uncertainty metrics are calculated and flagged for extrapolated regions; the system MUST output `data/processed/model_validation_report.json` containing a field `uncertainty_variance` for each point. `uncertainty_variance` is the variance of predictions across LOSO-CV splits.
5. **Flow Control**: If US-1 passed but US-2 fails the R² threshold, the system logs the failure but does not exit with error, allowing for fallback analysis (e.g., Poisson Anomaly mode).

### US-3: Trade-Off Decoupling and Visualization
**As a** design engineer,
**I want** to visualize decoupled regions where **Bulk and Shear Moduli** are uncorrelated (or anomalous),
**So that** I can target specific compositional clusters for independent property tuning.

**Acceptance Criteria:**
1. K-Means clustering (on ilr-transformed data) identifies a "Decoupled Region" meeting the criteria in SC-002.
2. A sensitivity analysis is performed on the correlation threshold across the range [0.1, 0.9] with step 0.1, and the system MUST output `data/processed/sensitivity_analysis.csv` with a `robustness_score` column (defined as Jaccard Index stability).
3. A 2D plot is generated showing the Pareto frontier, empirical data, and the decoupled region.

## 5. Data Model

### AlloyEntry
- `composition`: string (e.g., "Fe0.8Ni0.2")
- `bulk_modulus`: float (GPa)
- `shear_modulus`: float (GPa)
- `elements`: list of strings
- `metadata`: dict (source, temperature, etc.)

### ClusterAnalysis
- `cluster_id`: int
- `correlation_coefficient`: float
- `residual_variance`: float (if Poisson mode)
- `size`: int

### SensitivityAnalysis
- `threshold`: float
- `robustness_score`: float (Jaccard Index)

## 6. Constraints & Assumptions
- **Hardware**: CPU-only execution (max 2 cores, <7GB RAM).
- **Data Source**: OQMD via HuggingFace (`OQMD/elastic_properties`).
- **Target Properties**: **Bulk and Shear Moduli** only.
- **Runtime**: NSGA-II optimization must complete within 6 hours.
- **Statistical Rigor**: All claims of "significance" must be backed by defined statistical tests (e.g., permutation, bootstrap) with explicit null distributions.
- **Physics Constraint**: The analysis MUST account for the physical coupling of Bulk and Shear Moduli via Poisson's ratio, as defined in FR-000 and SC-002.

## 7. Appendix
- References to DFT proxy literature for Bulk/Shear Moduli as mechanical surrogates.
- Rule of Mixtures calculation methodology for theoretical bounds.
- Isometric Log-Ratio (ilr) transform methodology for compositional data.
- Poisson's Ratio constraint equation: $G = 3K(1-2\nu)/2(1+\nu)$.