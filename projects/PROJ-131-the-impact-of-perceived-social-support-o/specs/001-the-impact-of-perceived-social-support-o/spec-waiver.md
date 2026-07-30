# Spec Waiver: Exclusion of GSS 2022 and Dual-Dataset Requirements

**Date**: 2023-11-15
**Project**: PROJ-131-the-impact-of-perceived-social-support-o
**Task**: T041 (Kickback Task Fallback)

## Context

The original specification (v1.0) required a dual-dataset approach (FR-001, FR-002) utilizing both the Cyberbullying Survey 2021 and the General Social Survey (GSS) 2022 to construct the analysis cohort. This approach was intended to increase sample size and generalizability.

## Reason for Waiver

A methodological review (see `plan.md`, Section "Methodological Rationale") identified a critical flaw in the dual-dataset design:
1. **Confounding**: The two datasets differ significantly in sampling methodology, demographic distribution, and question phrasing. Merging them introduces a dataset-source confound that is perfectly collinear with the specific measures of social support and harassment, rendering interaction terms uninterpretable.
2. **Missing Measures**: The GSS 2022 dataset lacks the specific PCL-5 items required for the PTSD outcome measure, making a unified analysis impossible without imputation that would violate data integrity constraints.

Consequently, the PR to merge the dual-dataset requirements into the main spec was not merged by the deadline of 2023-11-15.

## Waiver Details

This document formally waives the following requirements for this feature branch:
- **FR-001**: Requirement to ingest and merge GSS 2022.
- **FR-002**: Requirement to harmonize variables across two distinct datasets.
- **US-1**: Requirement to construct a cohort from multiple sources.

**Replacement Requirement**:
- **FR-001-Single**: Ingest and process the Cyberbullying Survey 2021 as a single source.
- **US-1-Single**: Construct the analysis cohort exclusively from the Cyberbullying Survey 2021.

## Authorization

This waiver is authorized by the project lead to allow the pipeline (T012+) to proceed with a methodologically sound single-dataset approach. All subsequent analysis tasks (T012-T030) shall assume the single-dataset context.

**Status**: Active
**Impact**: The pipeline will no longer attempt to load GSS 2022. Any code attempting to load GSS 2022 must be removed or guarded.