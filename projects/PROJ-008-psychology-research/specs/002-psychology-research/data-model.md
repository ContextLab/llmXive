# Data Model: Mindfulness Components and Delivery Formats in ASD Social Skills

## Overview

This document defines the data structures used for ingestion, cleaning, and analysis. All data flows from raw API responses to a normalized CSV, validated against YAML schemas.

## Entity Definitions

### 1. Study (Raw & Intermediate)
Represents a single clinical trial record retrieved from an API.

*   `study_id`: Unique identifier (e.g., NCT number, OSF ID).
*   `source`: Origin (e.g., "ClinicalTrials.gov", "OSF").
*   `title`: Study title.
*   `publication_date`: Date of registration or publication.
*   `conditions`: List of conditions (must contain "Autism Spectrum Disorder" or "ASD").
*   `age_min`: Minimum enrollment age (numeric).
*   `age_max`: Maximum enrollment age (numeric).
*   `intervention_description`: Raw text description of the intervention.
*   `control_description`: Raw text description of the control.
*   `outcome_measures`: List of outcome measures (e.g., "SRS-2", "ABC").
*   `status`: Study status (e.g., "Completed", "Terminated").
*   `study_design`: Classification (e.g., "RCT", "Quasi-experimental", "Observational").

### 2. Cleaned Study (Processed)
The validated dataset used for analysis, derived from the Raw Study.

*   `study_id`: (PK)
*   `source`: (FK to raw source)
*   `intervention_component`: Categorical tag (e.g., "breath", "body_scan", "loving_kindness", "combined", "unknown").
*   `delivery_format`: Categorical tag (e.g., "caregiver_mediated", "child_led", "unknown").
*   `social_skill_domain`: Categorical tag (e.g., "peer_interaction", "emotional_recognition", "reciprocal_communication").
*   `n_intervention`: Sample size of intervention group.
*   `n_control`: Sample size of control group.
*   `pre_mean_int`: Mean pre-intervention score (intervention group).
*   `pre_sd_int`: Standard deviation pre-intervention (intervention group).
*   `post_mean_int`: Mean post-intervention score (intervention group).
*   `post_sd_int`: Standard deviation post-intervention (intervention group).
*   `pre_mean_ctrl`: Mean pre-intervention score (control group).
*   `pre_sd_ctrl`: Standard deviation pre-intervention (control group).
*   `post_mean_ctrl`: Mean post-intervention score (control group).
*   `post_sd_ctrl`: Standard deviation post-intervention (control group).
*   `follow_up_months`: Duration of follow-up (numeric or null).
*   `data_source_type`: Source of numeric data (e.g., "API", "PDF", "Reconstructed").
*   `coding_confidence`: Reliability of tags (e.g., "high", "low").
*   `exclusion_reason`: If excluded, the specific reason (e.g., "Age > 12", "Missing SD", "Non-RCT").

### 3. Effect Size (Derived)
Calculated metrics for each included study.

*   `study_id`: (FK)
*   `hedges_g`: Calculated effect size.
*   `se`: Standard error of the effect size.
*   `ci_lower`: Lower bound of 95% CI.
*   `ci_upper`: Upper bound of 95% CI.
*   `weight`: Weight in the meta-analysis.

## Data Flow

1.  **Ingestion**: `collector.py` fetches raw JSON from APIs -> `data/raw/`.
2.  **Extraction**: `extractor.py` parses JSON, applies regex for tags -> `data/interim/`.
3.  **Cleaning**: `cleaner.py` validates against `contracts/cleaned_study.schema.yaml`, logs exclusions -> `data/processed/clean_studies.csv`.
4.  **Analysis**: `effect_sizes.py` reads CSV, calculates metrics -> `data/processed/effect_sizes.csv`.
5.  **Aggregation**: `meta_analysis.py` aggregates results -> `data/processed/results.json`.

## Constraints

*   **Age Range**: Must be 6-12. Studies with `age_max < 6` or `age_min > 12` are excluded.
*   **Diagnosis**: Must explicitly mention ASD.
*   **Study Design**: Must be "RCT" for primary meta-analysis.
*   **Missing Data**: If `pre_sd` or `post_sd` is missing and cannot be reconstructed, the study is excluded.
*   **Multiple Arms**: If multiple intervention arms exist, the control group is split proportionally or the most relevant arm is selected (logged).