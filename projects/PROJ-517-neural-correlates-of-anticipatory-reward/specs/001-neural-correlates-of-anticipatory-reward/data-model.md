# Data Model: Neural Correlates of Anticipatory Reward Processing

## Overview

This document defines the data structures used for ingestion, processing, and output. The data model is designed to be strict to ensure reproducibility and validation against the `contracts/` schemas.

## Entities

### 1. Raw Trial Metadata
Contains information about each trial, including reward magnitude and timing.

*   `trial_id`: Unique string identifier for the trial.
*   `reward_magnitude`: Float (μL). The volume of reward delivered.
*   `reward_timestamp`: Float (ms). Time of reward delivery relative to session start.
*   `cue_timestamp`: Float (ms). Time of the cue (if applicable).
*   `session_id`: String identifier for the recording session.

### 2. Raw Spike Data
Contains raw spike timestamps for each neuron.

*   `neuron_id`: Unique string identifier for the neuron.
*   `trial_id`: String identifier linking spike to trial.
*   `spike_timestamp`: Float (ms). Absolute timestamp of the spike.

### 3. Processed Feature Matrix (Analysis DataFrame)
The primary input for the GLM. One row per neuron-trial pair.

*   `trial_id`: String.
*   `neuron_id`: String.
*   `spike_count`: Integer. Number of spikes in the [-500ms, 0ms] window relative to `reward_timestamp`.
*   `reward_magnitude`: Float.
*   `is_valid_trial`: Boolean. True if the cue-reward delay allows for a valid -500ms window.

### 4. Model Output
Results from the GLM and permutation test.

*   `neuron_id`: String.
*   `coefficient`: Float. Estimated slope for `reward_magnitude`.
*   `std_error`: Float. Standard error of the coefficient.
*   `p_value_perm`: Float. P-value from the permutation test.
*   `p_value_corrected`: Float. Bonferroni-corrected p-value.
*   `dispersion_param`: Float. Estimated dispersion parameter.
*   `converged`: Boolean. Did the model converge?

## Schema Definitions

The data model is enforced via the following YAML schemas located in `contracts/`:
*   `contracts/dataset.schema.yaml`: Validates the input processed data.
*   `contracts/output.schema.yaml`: Validates the model results.
