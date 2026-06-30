# Data Model: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Entities

### Subject
Represents an individual participant.
- `subject_id` (str): Unique identifier (e.g., "STDT01").
- `age` (int): Age in years.
- `gender` (str): "M" or "F".
- `has_waking` (bool): True if waking resting-state data exists.
- `has_sleep` (bool): True if sleep data exists.

### WakingNetwork
Represents the functional connectivity graph derived from waking EEG.
- `subject_id` (str): Foreign key to Subject.
- `band` (str): "theta" or "alpha".
- `connectivity_matrix` (numpy.ndarray): Symmetric matrix of coherence values (0-1).
- `centrality_degree` (dict): {node_id: value}.
- `centrality_betweenness` (dict): {node_id: value}.
- `centrality_eigenvector` (dict): {node_id: value}.
- `global_coherence_mean` (float): Mean coherence across all pairs (covariate).

### SleepStageEpoch
Represents a 30-second segment of EEG data.
- `subject_id` (str): Foreign key to Subject.
- `stage_label` (str): "Wake", "N1", "N2", "N3", "REM".
- `epoch_index` (int): Sequential index of the epoch.
- `plv_score` (float): Phase Lag Index for this epoch.

### SubjectMetrics
Aggregated metrics per subject per sleep stage.
- `subject_id` (str): Foreign key to Subject.
- `stage_label` (str): "N1", "N2", "N3", "REM".
- `mean_pli` (float): Mean PLI across all epochs of this stage.
- `n_epochs` (int): Number of epochs included.
- `centrality_degree_mean` (float): Mean degree centrality across nodes.
- `centrality_betweenness_mean` (float): Mean betweenness centrality across nodes.
- `centrality_eigenvector_mean` (float): Mean eigenvector centrality across nodes.
- `waking_night_id` (str): Identifier for the waking recording night (e.g., date or file hash).
- `sleep_night_id` (str): Identifier for the sleep recording night.
- `temporal_proximity` (bool): True if `waking_night_id` == `sleep_night_id`.

### AnalysisResult
Results of the LME correlation analysis.
- `metric_name` (str): "degree", "betweenness", "eigenvector".
- `stage_label` (str): "N1", "N2", "N3", "REM".
- `band` (str): "theta", "alpha".
- `correlation_coefficient` (float): LME fixed effect coefficient for the centrality metric.
- `p_value_raw` (float): Unadjusted p-value.
- `p_value_corrected` (float): FDR-corrected p-value.
- `significant` (bool): True if corrected p < 0.05.
- `method` (str): "lme".
- `global_connectivity_coefficient` (float): LME coefficient for the global coherence covariate.
- `covariate_used` (bool): True if global coherence was included in the model.

## Data Flow

1. **Raw**: `.edf` files from PhysioNet.
2. **Processed**: Cleaned epochs (`.npy` or `.h5`), connectivity matrices (`.npy`).
3. **Metrics**: `SubjectMetrics.csv` (one row per subject per stage, includes night IDs).
4. **Results**: `AnalysisResult.json` (LME stats).