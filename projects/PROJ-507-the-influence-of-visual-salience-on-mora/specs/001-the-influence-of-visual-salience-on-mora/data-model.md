# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## 1. Overview

This document defines the data structures used throughout the project, ensuring alignment with the **Data Hygiene** and **Single Source of Truth** principles of the project constitution. Data is organized into three main categories: **Stimuli**, **Responses**, and **Analysis Outputs**.

## 2. Entity Definitions

### 2.1 Scenario
A morally ambiguous visual situation.
*   **`scenario_id`** (string): Unique identifier (e.g., `SCN_001`).
*   **`source_dataset`** (string): Name of the source (e.g., "Visual_Genome_Subset", "Pexels_Public").
*   **`original_image_path`** (string): Relative path to the raw image in `data/raw/`.
*   **`ambiguity_label`** (string): "ambiguous" or "excluded".
*   **`target_region`** (string): Description of the region manipulated (e.g., "vehicle", "person").

### 2.2 Stimulus Variant
A specific manipulated version of a Scenario.
*   **`stimulus_id`** (string): Unique identifier (e.g., `SCN_001_LOW`, `SCN_001_MED`).
*   **`scenario_id`** (string): Foreign key to `Scenario`.
*   **`salience_level`** (string): "low", "medium", "high".
*   **`manipulation_params`** (object): JSON object containing `contrast_factor`, `brightness_factor`.
*   **`image_path`** (string): Relative path to the manipulated image in `data/processed/`.
*   **`semantic_preservation_score`** (float): SSIM or IoU score (if available).

### 2.3 Participant
An individual completing the survey.
*   **`participant_id`** (string): Unique anonymized ID (e.g., `P001`).
*   **`start_timestamp`** (datetime): ISO 8601 format.
*   **`end_timestamp`** (datetime): ISO 8601 format.
*   **`is_valid`** (boolean): Flag indicating if the participant passed data cleaning (e.g., no straight-lining).

### 2.4 Response
A single data point linking a Participant to a Stimulus Variant.
*   **`response_id`** (string): Unique identifier.
*   **`participant_id`** (string): Foreign key to `Participant`.
*   **`stimulus_id`** (string): Foreign key to `Stimulus Variant`.
*   **`blame_rating`** (integer): 1 to 7.
*   **`timestamp`** (datetime): ISO 8601 format.

### 2.5 Analysis Result
The output of the statistical analysis (Linear Mixed-Effects Model).
*   **`analysis_id`** (string): Unique identifier.
*   **`model_type`** (string): "Linear_Mixed_Effects_Model".
*   **`fixed_effects`** (object): Dictionary of fixed effect coefficients (e.g., `{"salience_high": 0.5, "salience_medium": 0.2}`).
*   **`random_effects_variance`** (object): Dictionary of random effect variances (e.g., `{"participant": 0.1, "scenario": 0.05}`).
*   **`p_value`** (float): Raw p-value for the main effect of salience.
*   **`p_value_corrected`** (float): Bonferroni-corrected p-value.
*   **`effect_size`** (float): Partial eta-squared ($\eta_p^2$) or marginal R-squared.
*   **`ci_lower`** (float): Lower bound of 95% CI.
*   **`ci_upper`** (float): Upper bound of 95% CI.
*   **`convergence_status`** (string): "converged", "warning", "failed".

## 3. Data Flow

1.  **Ingestion**: Raw images → `Scenario` table.
2.  **Manipulation**: `Scenario` → `Stimulus Variant` table (images saved to disk).
3.  **Collection**: `Stimulus Variant` + `Participant` → `Response` table.
4.  **Cleaning**: `Response` → Filtered `Response` (excluding invalid participants).
5.  **Analysis**: Filtered `Response` → `Analysis Result` table.
6.  **Reporting**: `Analysis Result` → Paper (read-only).

## 4. File Formats

*   **Stimuli**: PNG/JPG (in `data/processed/`).
*   **Tabular Data**: Parquet (for efficiency) or CSV (for readability) in `data/survey/`.
*   **Analysis Outputs**: JSON (for machine readability) in `data/analysis/`.
