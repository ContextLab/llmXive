# Project Specification: Multi-Property Trade-Offs in Alloy Design Using Public Compositional Data

## Version History

- **v1.0 (Initial Draft)**: Focused on Yield Strength and Elongation as primary targets.
- **v1.1 (Pivot to DFT Proxies)**: Updated to target **Bulk and Shear Moduli** as surrogates for mechanical properties to leverage high-throughput DFT databases (OQMD).
- **v1.2 (Refined Constraints & Clustering)**: Explicitly defined **Bulk and Shear Moduli** as the sole optimization targets. Updated Success Criteria to include K-Means clustering for decoupling analysis and Rule of Mixtures bounds.
- **v1.3 (Convergence Revision)**: Resolved contradictions between SC-003 and Constitution Principle VII; added statistical validation (permutation test) to SC-002; mandated isometric log-ratio (ilr) transform in FR-005; defined sensitivity analysis artifacts in FR-006; clarified stop conditions and uncertainty metrics in User Stories.

## 1. Executive Summary

This project aims to identify alloy compositions that optimize the trade-off between **Bulk Modulus** (resistance to uniform compression) and **Shear Modulus** (resistance to shear deformation). Unlike previous iterations focusing on yield strength, we utilize **Bulk and Shear Moduli** as DFT-derived proxies to access larger, high-quality public datasets (OQMD) and ensure physical consistency in our surrogate models.

## 2. Functional Requirements

### FR-001: Data Ingestion
The system must ingest compositional data and corresponding **Bulk and Shear Moduli** values from the OQMD dataset via HuggingFace. It must filter for entries where both moduli are positive and non-null.

### FR-002: Composition Encoding
The system must encode alloy compositions into feature vectors using elemental fractions and periodic descriptors (atomic radius, electronegativity) for every element present in the composition.

### FR-003: Surrogate Modeling
The system must train separate Gradient Boosting Regressors to predict **Bulk Modulus** and **Shear Modulus** from the encoded composition features. Models must be validated using Leave-One-System-Out Cross-Validation (LOSO-CV).

### FR-004: Pareto Optimization
The system must generate a Pareto frontier of optimal **Bulk and Shear Moduli** combinations using a genetic algorithm (NSGA-II) over a synthetic compositional space constrained strictly within the convex hull of the training data. The system MUST calculate prediction uncertainty via cross-validation variance and flag any points approaching the hull boundary (distance < 5% of hull radius) in the output.

### FR-005: Decoupling Analysis
The system must perform K-Means clustering on the compositional space to identify regions where **Bulk and Shear Moduli** exhibit low correlation (decoupled regions). To ensure geometric validity, the system MUST apply an isometric log-ratio (ilr) transform to the compositional data (elemental fractions) before clustering.

### FR-006: Sensitivity Analysis
The system must perform a sensitivity analysis on the correlation threshold used to define "decoupled" regions. The system MUST sweep the threshold across a range of [0.1, 0.9] in steps of 0.1, calculate the stability of cluster assignments, and output a CSV file `data/processed/sensitivity_analysis.csv` containing a `robustness_score` for each threshold.

## 3. Success Criteria

### SC-001: Model Performance
The surrogate models for **Bulk and Shear Moduli** must achieve an R² score > 0.6 on the LOSO-CV test sets.

### SC-002: Decoupling Identification
The system must identify at least one compositional cluster where the correlation coefficient between **Bulk and Shear Moduli** is significantly lower than the global correlation. "Significantly lower" is defined as a delta > 0.2 verified by a permutation test (1000 iterations, p < 0.05).

### SC-003: Pareto Frontier Quality
The generated Pareto frontier must contain non-dominated points that maximize coverage within and extend to the boundary of the empirical convex hull of the training data, respecting **DFT-derived physical bounds (Rule of Mixtures for Bulk/Shear)**.

## 4. User Stories

### US-1: Data Extraction and Composition Encoding
**As a** materials scientist,
**I want** to ingest public alloy data filtered for **Bulk and Shear Moduli**,
**So that** I can encode compositions and prepare a clean dataset for modeling.

**Acceptance Criteria:**
1. The system loads data from `OQMD/elastic_properties` and filters for valid **Bulk and Shear Moduli**.
2. The output CSV (`data/processed/encoded_alloys.csv`) contains no nulls in key columns.
3. Feature vectors include at least two periodic descriptors per element.
4. If valid entries < 500, the system MUST exit with error code 1 and log a critical error stating "Insufficient data for research validity; minimum 500 entries required."

### US-2: Surrogate Model Training and Pareto Generation
**As a** researcher,
**I want** to train models on **Bulk and Shear Moduli** and generate a Pareto frontier,
**So that** I can visualize the trade-offs and identify optimal regions.

**Acceptance Criteria:**
1. Models achieve R² > 0.6 on LOSO-CV.
2. A Pareto frontier is generated using NSGA-II with a fixed time budget.
3. Synthetic points are clamped to physical limits (moduli > 0) and strictly within the convex hull.
4. Uncertainty metrics are calculated and flagged for extrapolated regions; the system MUST output `data/processed/model_validation_report.json` containing a field `uncertainty_variance` for each point.

### US-3: Trade-Off Decoupling and Visualization
**As a** design engineer,
**I want** to visualize decoupled regions where **Bulk and Shear Moduli** are uncorrelated,
**So that** I can target specific compositional clusters for independent property tuning.

**Acceptance Criteria:**
1. K-Means clustering (on ilr-transformed data) identifies a "Decoupled Region" with minimum correlation.
2. A sensitivity analysis is performed on the correlation threshold across the range [0.1, 0.9] with step 0.1, and the system MUST output `data/processed/sensitivity_analysis.csv` with a `robustness_score` column.
3. A 2D plot is generated showing the Pareto frontier, empirical data, and the decoupled region.

## 5. Data Model

### AlloyEntry
- `composition`: string (e.g., "Fe0.8Ni0.2")
- `bulk_modulus`: float (GPa)
- `shear_modulus`: float (GPa)
- `elements`: list of strings
- `metadata`: dict (source, temperature, etc.)

## 6. Constraints & Assumptions
- **Hardware**: CPU-only execution (max 2 cores, <7GB RAM).
- **Data Source**: OQMD via HuggingFace (`OQMD/elastic_properties`).
- **Target Properties**: **Bulk and Shear Moduli** only.
- **Runtime**: NSGA-II optimization must complete within 6 hours.
- **Statistical Rigor**: All claims of "significance" must be backed by defined statistical tests (e.g., permutation, bootstrap).

## 7. Appendix
- References to DFT proxy literature for Bulk/Shear Moduli as mechanical surrogates.
- Rule of Mixtures calculation methodology for theoretical bounds.
- Isometric Log-Ratio (ilr) transform methodology for compositional data.