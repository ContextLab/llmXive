# Specification: Molecular Descriptor Correlation Analysis

## User Stories
1. **US1**: As a researcher, I want to download and clean ChEMBL data so that I can analyze molecular properties.
2. **US2**: As a data scientist, I want to train regression models on the cleaned data to predict drug-likeness.
3. **US3**: As a stakeholder, I want to visualize the model performance and feature importance to understand the results.

## Functional Requirements
- FR-001: Download ChEMBL 33 SQLite dataset.
- FR-002: Sanitize molecules and filter for specific targets.
- FR-003: Calculate 2D molecular descriptors.
- FR-004: Split data for training and testing.
- FR-005: Train Linear Regression and Random Forest models.
- FR-006: Evaluate models and generate metrics.
- FR-007: Generate visualizations.

## Non-Functional Requirements
- SC-001: Memory usage must not exceed 7GB.
- SC-002: Pipeline must complete within 6 hours.
- SC-003: All artifacts must be versioned and hashed.
