# Plan Waiver Log: FR-006 Sensitivity Sweep

**Date:** 2024-05-21
**Project:** Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution (PROJ-254)
**Task ID:** T052
**Status:** Ratified

## Executive Summary

This document formally ratifies the Plan's decision to **WAIVE** the requirement for **FR-006 (Sensitivity Sweep)** as specified in the original feature specification. In its place, the project adopts **Cook's Distance (T032)** as the approved robustness check for the regression analysis phase.

## Context and Conflict

The original Feature Specification (FR-006) mandated a "Sensitivity Sweep" to test the robustness of the linear regression results against variations in hyperparameters or data exclusion thresholds.

However, the Project Plan (Phase 5, User Story 3) explicitly noted:
> "FR-006 (Sensitivity Sweep) is waived per Plan; Cook's Distance (T032) is the replacement."

This created a direct conflict between the Spec requirement (FR-006) and the Plan's architectural decision. To resolve this and ensure the pipeline proceeds with a coherent, approved methodology, this waiver is formally documented.

## Waiver Details

| Item | Original Requirement | Waived Status | Replacement |
|:--- |:--- |:--- |:--- |
| **ID** | FR-006 | **WAIVED** | T032 |
| **Name** | Sensitivity Sweep | N/A | Cook's Distance Analysis |
| **Purpose** | Test model stability via parameter sweeping | N/A | Identify high-leverage outliers affecting regression fit |
| **Rationale** | Computationally expensive; less effective for small N time-series | **Adopted** | Cook's Distance is statistically rigorous for detecting influential points in linear regression, specifically suited for the temporal trend analysis in this project. It provides a focused robustness check without the overhead of a full hyperparameter sweep. |

## Implementation Reference

The replacement robustness check is implemented in:
- **Task:** T032
- **File:** `src/code/regression.py`
- **Function:** `calculate_cooks_distance`
- **Output:** `data/derived/cooks_distance_report.csv`

This implementation calculates Cook's Distance for each data point in the linear regression model (Year vs. Mean Off-Diagonal Similarity) to identify any single year that disproportionately influences the slope and intercept estimates.

## Governance Approval

This waiver resolves the conflict between Spec FR-006 and the Plan. The pipeline shall proceed using the Cook's Distance methodology as the sole approved robustness check for the regression phase.

**Approved By:** Automated Science Pipeline Governance
**Effective Date:** Immediate upon generation of this log.