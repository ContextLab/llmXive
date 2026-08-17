# Project Scope Statement: Neuro-Symbolic Learning Networks

## Overview

This document defines the scope of the research project "Neuro-Symbolic Learning Networks: Bridging Neural and Symbolic Reasoning in Education". It clarifies the datasets, methodologies, and boundaries of the investigation.

## Dataset Scope

### Primary Dataset: ASSISTments 2009-2010

- **Source**: Hugging Face Datasets (`assistments/2009-2010`)
- **Format**: CSV with columns including `problem_id`, `skill`, `correct`, `first_attempt`, `num_attempts`
- **Rationale**: The ASSISTments dataset provides a well-established benchmark for educational data mining, containing real student interaction data with math problems. It supports the investigation of both neural and symbolic explanation generation for algebra, geometry, and arithmetic problems.

### Excluded Dataset: Khan Academy

- **Status**: EXCLUDED from project scope
- **Reasoning**: Per the project planning documents (plan.md), the Khan Academy dataset was intentionally removed from the scope. This decision was made to:
 1. Focus resources on a single, well-documented dataset
 2. Reduce complexity in the data ingestion pipeline
 3. Align with FR-001 scope reduction requirements
 4. Ensure deeper analysis of the ASSISTments data rather than shallow coverage of multiple sources

## Methodological Boundaries

### Included Components

1. **Neural Explanation Generation**: Using TinyLlama/TinyLlama-Chat for natural language explanations
2. **Symbolic Explanation Generation**: Rule-based engine for algebraic and geometric reasoning
3. **Neuro-Symbolic Integration**: Combining neural narratives with symbolic traces
4. **Student Simulation**: Bayesian Knowledge Tracing (BKT) model for simulating student responses
5. **Comparative Analysis**: Mixed-effects regression and effect size calculations

### Excluded Components

1. **GPU-Dependent Models**: All models must run on CPU (FR-008 constraint)
2. **Real-time Student Interaction**: The system simulates rather than interacts with live students
3. **Additional Datasets**: No expansion to other educational datasets beyond ASSISTments
4. **Longitudinal Studies**: The project focuses on cross-sectional analysis rather than long-term tracking

## Calibration Requirements

- **Human Pilot Data**: Required for calibration (FR-010). The pipeline must halt if human pilot data is missing (<50 records).
- **Real Student Data**: Minimum 200 records required for full analysis (FR-011). If unavailable, analysis proceeds in "simulated-only" mode with appropriate limitation flags.

## Success Criteria

The project is considered successful if:
1. Three distinct explanation types are generated and validated for distinctness (similarity < 0.95)
2. Simulation logs are generated for at least 2,000 students per condition
3. Calibration metrics meet thresholds (RMSE < 0.15, difference < 0.02)
4. Comparative analysis produces statistically valid results (p < 0.05) with CI width ≤ 0.20

## Version History

- **v1.0**: Initial scope definition, excluding Khan Academy dataset
- **Last Updated**: 2024-01-15

## References

- Plan.md: Implementation plan for the project
- FR-001: Dataset requirements
- FR-007: Timeout handling requirements
- FR-010: Calibration requirements
- FR-011: Real student data requirements