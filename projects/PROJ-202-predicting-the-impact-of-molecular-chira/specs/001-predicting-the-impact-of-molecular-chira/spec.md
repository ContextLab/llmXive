# Feature Specification: Predicting the Impact of Molecular Chirality on Flavor Perception

**Feature Branch**: `001-predict-chirality-flavor`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Molecular Chirality on Flavor Perception"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Docking Pipeline (Priority: P1)

As a researcher, I want to download aroma molecule data and olfactory receptor structures, then perform CPU-only molecular docking to generate binding affinity predictions for enantiomeric pairs, so that I can establish a baseline measure of stereoselective binding.

**Why this priority**: This is the foundational computation. Without docking scores for enantiomers, no comparison or perception correlation is possible. It represents the minimum viable computational experiment.

**Independent Test**: The pipeline downloads a fixed subset of molecules (e.g., 10 enantiomeric pairs) and receptors (e.g., 5), runs AutoDock Vina, and outputs a CSV of binding affinities within 2 hours on a CPU-only runner.

**Acceptance Scenarios**:

1. **Given** a list of 10 enantiomeric SMILES and 5 receptor PDB files, **When** the docking script executes, **Then** it outputs a CSV containing docking scores (kcal/mol) and RMSD values for all 100 ligand-receptor combinations (10 pairs * 2 enantiomers * 5 receptors).
2. **Given** a GitHub Actions free-tier runner (2 CPU, 7GB RAM), **When** the pipeline runs, **Then** the total wall-clock time does not exceed 2 hours.

---

### User Story 2 - MD Refinement & Interaction Fingerprinting (Priority: P2)

As a researcher, I want to run short molecular dynamics simulations on the top-scoring docked complexes to extract interaction fingerprints, so that I can validate docking poses with dynamic stability metrics.

**Why this priority**: Docking is static; MD adds conformational validity. This increases confidence in the binding affinity predictions but is secondary to generating the initial scores.

**Independent Test**: For the top 5 ranked ligand-receptor complexes, the system runs 10ns MD simulations and outputs interaction fingerprint matrices (hydrogen bonds, hydrophobic contacts) within 3 hours.

**Acceptance Scenarios**:

1. **Given** the top 5 docked complexes from US-1, **When** the MD refinement script executes, **Then** it produces trajectory files and a summary CSV of interaction frequencies over 10ns.
2. **Given** 2 CPU cores, **When** the MD simulation runs, **Then** it completes without memory errors (≤7 GB RAM usage) and within 3 hours total.

---

### User Story 3 - Statistical Analysis & Perception Correlation (Priority: P3)

As a researcher, I want to statistically compare enantiomeric binding differences and correlate them with human sensory ratings, so that I can determine if stereoselectivity predicts flavor perception nuances.

**Why this priority**: This answers the research question directly. It requires the outputs of US-1 and US-2 plus external sensory data. It is the "value-add" analysis.

**Independent Test**: The analysis script performs paired Wilcoxon tests on docking scores and Spearman correlations with sensory ratings, outputting p-values and effect sizes.

**Acceptance Scenarios**:

1. **Given** the docking scores from US-1 and sensory ratings from FlavorDB, **When** the statistical analysis runs, **Then** it outputs a table of p-values for paired differences and correlation coefficients.
2. **Given** multiple hypothesis tests (>5 pairs), **When** the analysis runs, **Then** it applies False Discovery Rate (FDR) correction and reports adjusted p-values.

---

### Edge Cases

- What happens when FlavorDB lacks sensory ratings for a specific enantiomer? (System excludes that pair from correlation analysis but retains docking results).
- How does system handle AlphaFold models with low confidence (pLDDT < 70) in the binding pocket? (System flags these pairs for manual review or excludes them based on a pLDDT threshold).
- What happens if docking fails for a specific ligand (e.g., steric clash)? (System logs the error and assigns a null score, excluding from statistical mean).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download ligand SMILES and receptor PDB files from FlavorDB and AlphaFold databases respectively, limiting the initial dataset to ≤ 20 enantiomeric pairs and ≤ 5 receptors to ensure compute feasibility (See US-1).
- **FR-002**: System MUST perform molecular docking using AutoDock Vina in CPU-only mode, explicitly disabling any GPU/CUDA acceleration flags (See US-1).
- **FR-003**: System MUST define a binding affinity difference threshold of ≥ 0.5 kcal/mol to classify stereoselectivity, justified by typical Vina scoring error margins (See US-1).
- **FR-004**: System MUST run MD refinement on at most the top 10 ligand-receptor complexes (by docking score) for 10ns duration using OpenMM on 2 CPU cores to fit within 6h total runtime (See US-2).
- **FR-005**: System MUST perform paired Wilcoxon signed-rank tests to compare enantiomeric docking scores, framing results as associational rather than causal (See US-3).
- **FR-006**: System MUST apply Benjamini-Hochberg FDR correction for multiple comparisons when testing >5 receptor-ligand pairs (See US-3).
- **FR-007**: System MUST perform a sensitivity analysis on the binding affinity threshold by sweeping values ∈ {0.4, 0.5, 0.6} kcal/mol and reporting variation in significance rates (See US-3).
- **FR-008**: System MUST exclude receptor models with pLDDT < 70 in the binding pocket region from the analysis to ensure measurement validity (See US-1).

### Key Entities *(include if feature involves data)*

- **Enantiomeric Pair**: A pair of molecules with identical SMILES connectivity but opposite chirality, linked by a unique compound ID.
- **Receptor Complex**: A specific pairing of a receptor structure and a ligand, storing docking score, RMSD, and MD interaction metrics.
- **Sensory Rating**: A psychophysical value (e.g., intensity, pleasantness) associated with a specific compound ID in FlavorDB.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total pipeline runtime is measured against the 6-hour GitHub Actions free-tier limit (See US-1).
- **SC-002**: Memory usage is measured against the 7 GB RAM constraint during MD simulation peaks (See US-2).
- **SC-003**: Statistical significance of stereoselectivity is measured against the adjusted p-value threshold (α < 0.05 after FDR correction) (See US-3).
- **SC-004**: Correlation strength between computational metrics and perception is measured against the Spearman’s ρ coefficient magnitude (See US-3).

## Assumptions

- **Compute Constraint**: The analysis assumes a CPU-only environment (no CUDA/GPU) and will sample the dataset (≤20 pairs, ≤5 receptors) to ensure completion within 6 hours on 2 cores.
- **Data Availability**: It is assumed that FlavorDB contains sensory rating fields for at least 50% of the selected enantiomeric pairs; missing ratings will be excluded from correlation analysis (See `[NEEDS CLARIFICATION: Does FlavorDB contain receptor-specific sensory ratings for the selected enantiomers?]`).
- **Threshold Justification**: The 0.5 kcal/mol binding difference threshold is assumed to be a standard community approximation for docking distinguishability, subject to the sensitivity analysis in FR-007.
- **Methodological Framing**: The study assumes an observational design; any correlation between binding and perception is framed as associational, not causal, due to lack of randomization.
