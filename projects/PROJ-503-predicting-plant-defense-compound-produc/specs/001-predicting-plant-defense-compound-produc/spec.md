# Feature Specification: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Feature Branch**: `001-predict-plant-defense`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – End‑to‑end data acquisition & pairing (Priority: P1)

A computational biologist wants to obtain a paired dataset of gene‑expression profiles and defense‑metabolite concentrations for *Arabidopsis* and *Solanum* samples that were subjected to herbivore stress, so that downstream modelling can be performed.

**Why this priority**: Without correctly paired input data the entire predictive pipeline cannot function; this is the foundational step.

**Independent Test**: Run the data‑download module on the specified GEO series IDs and Metabolomics Workbench experiment IDs and verify that every expression sample has a matching metabolite record from the same biological sample.

**Acceptance Scenarios**:

1. **Given** a list of GEO series IDs annotated as "herbivore stress", **When** the download script is executed, **Then** it creates a CSV file containing normalized TPM/FPKM values for each sample and logs any missing files.
2. **Given** the same list of experiment IDs on Metabolomics Workbench, **When** the metabolite‑retrieval script runs, **Then** it produces a CSV of log‑transformed metabolite concentrations aligned by the experimental sample identifier (not condition ID alone).

---

### User Story 2 – Feature selection & preprocessing (Priority: P2)

A researcher needs to isolate expression features that belong to known defense‑biosynthetic pathways and ensure both expression and metabolite matrices are properly normalized before modelling.

**Why this priority**: Accurate feature selection reduces dimensionality, mitigates collinearity, and respects biological relevance.

**Independent Test**: Execute the feature‑selection module and confirm that the resulting feature matrix contains only genes whose KEGG IDs map to terpenoid, alkaloid, or phenylpropanoid pathways.

**Acceptance Scenarios**:

1. **Given** a full expression matrix and a KEGG pathway list, **When** the selection script runs, **Then** the output matrix includes exactly those rows whose gene IDs appear in the pathway list and excludes all others.

---

### User Story 3 – Predictive modelling & evaluation (Priority: P3)

A data scientist wants to train a Ridge Regression model to predict defense‑metabolite abundance from the selected gene‑expression features and assess performance using cross‑validation and permutation testing.

**Why this priority**: This story delivers the scientific answer to the research question and generates the quantitative results required for publication.

**Independent Test**: Run the modelling script on the paired dataset and verify that it reports RMSE, Pearson r, and a permutation‑test p‑value for each metabolite.

**Acceptance Scenarios**:

1. **Given** a paired feature‑target matrix, **When** the Ridge Regression model is trained with 5‑fold cross‑validation, **Then** the script outputs the mean RMSE and Pearson correlation coefficient across folds for each metabolite.
2. **Given** the same trained model, **When** a permutation test with 1 000 iterations is performed, **Then** the script reports a two‑sided p‑value ≤ 0.05 for metabolites that show a true predictive signal.

### Edge Cases

- **What happens when a GEO sample lacks a corresponding metabolite measurement from the same biological sample?**  
  → The pipeline logs the mismatch in JSON format to `logs/data_pairing.json` with fields `{sample_id, expression_source, metabolite_source, reason: "no_sample_level_pair"}` and excludes the sample from modelling.

- **How does the system handle genes with zero variance across all samples?**  
  → Genes with variance < 1e-10 are automatically dropped during preprocessing and logged to `logs/feature_filtering.csv` with columns `gene_id, variance, reason: "zero_variance"`.

- **What if a requested KEGG pathway ID is not found for a given species?**  
  → The pipeline falls back to the orthologous gene list from a closely related reference species (requiring ≥60% sequence identity) and documents the substitution in `docs/edge_cases.md` with the original gene ID, substituted gene ID, and sequence identity percentage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download processed gene‑expression matrices from GEO for the specified *Arabidopsis* and *Solanum* series that are annotated as herbivore‑stress experiments. (See US-1)  
- **FR-002**: System MUST retrieve matched targeted metabolomics data from the Metabolomics Workbench for the same biological samples (verified via sample-level metadata), not just experimental condition IDs. (See US-1)  
- **FR-003**: System MUST normalize expression values to TPM/FPKM, log‑transform metabolite concentrations, and filter out features with variance < 1e-10. (See US-2)  
- **FR-004**: System MUST select expression features that map to defense‑biosynthetic pathway genes using KEGG pathway IDs (e.g., terpenoid synthases, alkaloid enzymes). (See US-2)  
- **FR-005**: System MUST train a Ridge Regression model on the selected features, evaluate it with 5‑fold cross‑validation, and report RMSE and Pearson r for each metabolite. (See US-3)  
- **FR-006**: System MUST conduct a permutation test with 1 000 iterations to assess statistical significance of each model's predictive performance. (See US-3)  
- **FR-007**: System MUST apply a family‑wise error correction (Bonferroni) across all metabolites tested. (Methodological soundness – multiplicity)  
- **FR-008**: System MUST log runtime and resource usage and abort if total CPU time exceeds 4 hours on the CI runner. (See US-3, compute feasibility)  
- **FR-009**: System MUST validate sample‑level pairing feasibility before modeling; if <95% of samples have matched expression‑metabolite pairs from the same biological sample, the pipeline MUST halt with error code E-PAIRING and report the pairing rate. (See US-1, scientific soundness)  
- **FR-010**: System MUST apply species‑specific z‑score normalization and ComBat batch correction before training a cross‑species model to account for expression scale differences between *Arabidopsis* and *Solanum*. (See US-3, scientific soundness)

### Key Entities

- **ExpressionMatrix**: Rows = gene identifiers, Columns = sample IDs; values = TPM/FPKM.  
- **MetaboliteMatrix**: Rows = metabolite identifiers (defense compounds), Columns = sample IDs; values = log‑transformed concentrations.  
- **FeatureSet**: Subset of genes from ExpressionMatrix that belong to KEGG defense pathways.  
- **ModelArtifact**: Serialized Ridge Regression coefficients and evaluation metrics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pearson correlation coefficient (r) between predicted and observed abundance must be ≥ 0.5 for the metabolite with the highest Pearson r across the 5‑fold cross‑validation (See US-3).  
- **SC-002**: Permutation‑test p‑value for the metabolite with the highest Pearson r must be ≤ 0.05 after Bonferroni correction (See US-3, FR‑007).  
- **SC-003**: End‑to‑end pipeline (download → preprocessing → modelling) must complete within 4 hours on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM) (See FR‑008).  
- **SC-004**: Downloaded files from GEO and Metabolomics Workbench must match expected checksums (SHA-256) for ≥99% of requested experiment IDs (See US-1).  
- **SC-005**: At least ≥95% of expression samples must have matching metabolite records from the same biological sample (See US-1, FR-009).  
- **SC-006**: Feature selection must retain ≥75% of known defense pathway genes for each species, and zero‑variance filtering must document the count of removed genes in `logs/feature_filtering.csv` (See US-2, FR-003).  

## Assumptions

- **GEO availability**: The GEO series selected contain **herbivore‑stress** conditions for the target genotypes. [deferred: citation required] GEO contains herbivore‑stress experiments for both *Arabidopsis* and *Solanum* species. The pipeline will select experiments with explicit herbivore treatment annotations and exclude studies with only abiotic stress conditions.

- **Metabolomics Workbench data quality**: The Metabolomics Workbench experiments provide **quantitative measurements** for the defense metabolites of interest (e.g., specific terpenoids, alkaloids). [deferred: citation required] The pipeline will require ≥5 samples with quantified values per metabolite; metabolites below this threshold will be excluded from analysis.

- **KEGG pathway annotations**: KEGG pathway annotations for *Solanum* species cover ≥75% of known defense‑biosynthetic genes. [deferred: citation required] The pipeline will use ortholog mapping from *Arabidopsis* for unannotated *Solanum* genes, requiring ≥60% sequence identity for substitution. All substitutions will be logged and reported in the feature selection output.

- **Observational nature**: The relationship being examined is **observational**; therefore, all reported effects are associational, not causal.

- **Sample size for power**: Sample size is sufficient to achieve moderate statistical power for detecting r ≥ 0.5; a formal power analysis will be performed during implementation, with the required sample size noted as `[deferred]`.

- **Instrument validation**: All instruments used in the original metabolomics studies are **validated** (e.g., LC‑MS with published calibration curves), as reported in the source publications. [deferred: citation required]

- **Multicollinearity handling**: Gene expression predictors may be collinear; the Ridge penalty is assumed to mitigate multicollinearity, and collinearity diagnostics (VIF) will be reported.