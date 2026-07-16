# Specification: Predicting Protein-Protein Interactions

## User Stories
- US1: Build & Export Co-expression-based PPI Predictions
- US2: Quantitative Evaluation Against STRING
- US3: Functional Enrichment of Predicted Interactome

## Functional Requirements
- FR-004: Minimum correlation threshold of 0.75
- FR-014: Confound regression for expression-level and gene-length
- FR-032: Balanced negative sampling for evaluation
- FR-045: FDR correction on correlation p-values

## Non-Functional Requirements
- Reproducibility: Fixed random seed
- Validation: Schema enforcement for all outputs
- Performance: < 6h runtime on standard CI runner
