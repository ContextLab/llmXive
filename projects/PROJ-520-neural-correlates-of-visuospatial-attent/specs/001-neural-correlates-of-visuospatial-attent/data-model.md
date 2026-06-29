# Data Model: Neural Correlates of Visuospatial Attention Shifts During Simulated Navigation

## Entities

### Epoch
- **Definition**: A 2-second EEG segment centered on an attention shift event.
- **Attributes**:
  - `id`: Unique string identifier.
  - `condition`: Enum {active, passive}.
  - `participant_id`: String (from participants.tsv).
  - `start_time`: Float (seconds relative to event).
  - `signal`: Array[float] (channels × samples).
- **Constraints**: Must contain valid time-frequency features; ≤20% rejection rate for artifacts.

### Feature
- **Definition**: Mean power value for a specific frequency band at a specific electrode.
- **Attributes**:
  - `epoch_id`: Foreign key to Epoch.
  - `electrode`: Enum {P3, Pz, P4, F3, Fz, F4}.
  - `band`: Enum {alpha, beta}.
  - `power_db`: Float (0-100 dB).
- **Constraints**: Non-NaN values for ≥80% of epochs.

### Classifier
- **Definition**: LDA model trained on extracted features.
- **Attributes**:
  - `model_id`: Unique string identifier.
  - `accuracy`: Float (0-1).
  - `precision`: Float (0-1).
  - `recall`: Float (0-1).
  - `p_value`: Float (from permutation test).
- **Constraints**: Accuracy ≥65% (Constitution Principle VII); p-value ≤0.05.

### PermutationResult
- **Definition**: Results from permutation testing for classifier validation.
- **Attributes**:
  - `run_id`: Unique string identifier.
  - `iterations`: Integer (≥1000).
  - `p_value`: Float (empirical p-value).
  - `null_distribution`: Array[float] (permuted accuracy values).
  - `rejection_decision`: Boolean (whether null hypothesis rejected at α = 0.05).
- **Constraints**: Must be stored for reproducibility (Constitution Principle I).

## Relationships

- **Epoch** (1) → (N) **Feature** (One epoch yields multiple features across electrodes/bands).
- **Feature** (N) → (1) **Classifier** (Classifier trained on set of features).
- **Classifier** (1) → (1) **PermutationResult** (Single p-value per model run).
- **PermutationResult** (1) → (1) **StatisticalCorrection** (FWE-corrected p-values).

## Output Schema

- **participant_count**: Integer (number of participants in analysis).
- **epoch_count**: Integer (total epochs processed).
- **condition_distribution**: Object with active/passive counts.
- **preprocessing_metrics**: Object with rejection_rate and line_noise_residual.
- **feature_extraction**: Object with valid_epochs_ratio and electrodes_used.
- **classification_results**: Object with accuracy, precision, recall, p_value.
- **statistical_corrections**: Object with method and corrected_p_value.