# Data Model: Pipeline Validation - Investigating the Impact of Network Topology on Neural Entrainment (Simulated Data)

## Entities

### 1. Subject
Represents a single participant in the study.
* `subject_id` (string): Unique identifier (e.g., "100101").
* `source_dataset` (string): Origin of the data (e.g., "HCP", "Synthetic").

### 2. TopologyMetric
Network properties derived from fMRI connectivity.
* `subject_id` (string): Foreign key to Subject.
* `atlas` (string): Parcellation scheme used ("Schaefer", "AAL", "Power264").
* `clustering_coefficient` (float): Global clustering coefficient.
* `path_length` (float): Characteristic path length.
* `vif` (float): Variance Inflation Factor (calculated across the sample).

### 3. EntrainmentStrength
External metric of neural response (Synthetic or Real).
* `subject_id` (string): Foreign key to Subject.
* `metric_value` (float): Phase‑Locking Value or entrainment strength metric.
* `protocol` (string): Description of the stimulation (e.g., "10Hz Rhythmic" or "Synthetic").
* `data_source` (string): `"real"` if from a verified dataset, `"synthetic"` otherwise.

### 4. AnalysisResult
Aggregated statistical findings.
* `atlas` (string): Atlas used for this result.
* `metric_type` (string): "clustering" or "path_length".
* `correlation_r` (float): Spearman r (univariate).
* `partial_correlation_r` (float): Partial correlation r (controlling for the other metric).
* `p_value_raw` (float): Raw p-value (univariate).
* `p_value_partial` (float): Raw p-value (partial correlation).
* `p_value_adj` (float): Bonferroni‑corrected p-value (for partial correlation).
* `is_significant` (boolean): True if `p_value_adj < 0.05`.
* `effect_size_diff` (float): Absolute difference vs. Schaefer (null for Schaefer).
* `collinearity_warning` (string): "Collinearity Warning: VIF > 5" if applicable, else null.
* `power_warning` (string): "Power Warning: N < 30 (Exploratory)" if applicable, else null.
* `data_source` (string): `"real"` or `"synthetic"` indicating the origin of the entrainment metric.

## Data Flow

1. **Ingest**: Raw HCP (Parquet) + Synthetic Entrainment → `data/raw/`.
2. **Validate**: Check for `subject_id`, connectivity matrix, and `metric_value` column.
3. **Process**:
   * Compute Graph Metrics (if raw matrix provided) or load pre‑computed.
   * Merge on `subject_id` (inner join).
   * Record `data_source` flag.
4. **Analyze**:
   * Correlation → Bonferroni → **Partial Correlation**.
   * If `N < 30`, add `power_warning`.
   * If `VIF > 5`, flag as `collinearity_warning` but proceed with Partial Correlation.
5. **Output**: `data/processed/results.csv`, `artifacts/plots/`.