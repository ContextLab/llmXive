# Formal Scope Reduction Record

**Date**: 2023-10-27
**Project**: PROJ-265-assessing-the-impact-of-data-ordering-on
**Task ID**: T038
**Status**: Active (Recorded)

## Executive Summary

This document formally records the reduction of scope for Project PROJ-265. Specifically, Functional Requirements **FR-006**, **FR-007**, **FR-009**, and **FR-010** are removed from the active development scope due to the absence of a verified, programmatically accessible data source for the UCI dataset.

This decision aligns with the project's `plan.md` directive which states: "No user story work can begin until this phase is complete" and "Implementation tasks moved to 'Deferred / Blocked Requirements' section pending a verified data source."

## Removed Functional Requirements

The following requirements are hereby suspended and removed from the active iteration:

1. **FR-006: Real-World Data Loading & Error Handling**
 * *Original Scope*: Implement robust loading mechanisms for external UCI data with checksum verification and explicit error halting.
 * *Reason for Removal*: No verified URL or API endpoint exists for the required dataset. Implementing this logic without a target source constitutes speculative development.
 * *Related Tasks*: **T032** (Implementation of error handling logic).

2. **FR-007: Real-World Data Segmentation**
 * *Original Scope*: Segment large real-world datasets into manageable chunks for analysis.
 * *Reason for Removal*: Dependent on FR-006. Without real data to segment, this logic cannot be validated.
 * *Related Tasks*: **T032** (includes segment loading logic).

3. **FR-009: Stratified Reporting for Real-World Data**
 * *Original Scope*: Generate stratified reports based on estimated phi for real-world segments.
 * *Reason for Removal*: Requires real-world data segments (FR-007) to generate meaningful stratification bins.
 * *Related Tasks*: **T035** (Stratification logic and report generation).

4. **FR-010: Bias Block Bootstrap for Real Data**
 * *Original Scope*: Calculate bias blocks relative to real-world data estimates (since theoretical mean is unknown).
 * *Reason for Removal*: Dependent on the existence of real-world data segments. The synthetic AR(1) data (User Story 1) provides a known theoretical mean, making this specific requirement inapplicable to the current synthetic-only scope.
 * *Related Tasks*: **T033** (Alternative metrics implementation).

## Impact Analysis

### Active Scope (Synthetic Only)
The project will proceed exclusively with **User Story 1 (Synthetic AR(1) Data)** and **User Story 2 (Ordered vs. Shuffled Baselines)**.
* **Data Source**: Synthetic AR(1) series generated via `code/data_generation.py`.
* **Theoretical Mean**: Known (0.0), allowing for direct coverage probability calculation without FR-010's bias block estimation.
* **Validation**: All statistical tests (McNemar's, coverage degradation) are validated against synthetic ground truth.

### Blocked Scope
The following tasks are marked as **BLOCKED** and will not be executed until a verified data source is provided in `plan.md`:
* **T032**: Implement error handling and logging logic for real-world data.
* **T033**: Implement alternative metrics for real-world data.
* **T035**: Implement stratification logic and report for real-world results.

## Future Re-activation Criteria

These requirements may be re-included in a future iteration only if:
1. A verified, stable URL or API endpoint for the UCI dataset is identified and documented in `plan.md`.
2. The `data_loader.py` module is successfully tested against the real source (verifying checksums and segmentability).
3. The project timeline is updated to accommodate the increased computational cost of processing real-world data segments.

## Approval

This scope reduction is consistent with the project's risk management strategy to avoid fabrication of data (Constitution Principle III) and to ensure all execution paths are grounded in verified, real-world inputs.

*Recorded by: Automated Implementation Agent (T038)*
*Verified against: `tasks.md`, `plan.md`, `specs/001-assess-data-ordering-bootstrapping/`*