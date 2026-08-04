# Data Model: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## 1. Entity Definitions

### Subject
A unique participant in the dataset.
*   `subject_id` (string): Unique identifier (e.g., "01", "S01").
*   `age` (integer): Optional demographic.
*   `gender` (string): Optional demographic.

### Phase
A distinct temporal segment of the experiment.
*   `phase_id` (string): "baseline", "stress", "recovery".
*   `start_time` (float): Timestamp relative to session start.
*   `end_time` (float): Timestamp relative to session start.
*   `task_label` (string): BIDS task label (e.g., "rest", "tsst", "schandry").

### Metric
A derived quantitative value.
*   `metric_id` (string): "rmssd", "sdnn".
*   `value` (float): The calculated metric.
*   `phase_id` (string): Links to the phase.
*   `subject_id` (string): Links to the subject.
*   `quality_flag` (string): "valid", "noisy", "missing".

### InteroceptionScore
Behavioral performance on the Schandry task.
*   `subject_id` (string): Links to the subject.
*   `accuracy_score` (float): Ratio of correct counts (0.0 to 1.0).
*   `task_type` (string): "schandry".

## 2. Data Flow

1.  **Ingestion**: Raw ECG/PPG signals and BIDS metadata (`events.tsv`) are downloaded.
2.  **Audit**: `02_audit_metadata.py` parses `events.tsv` to populate a `AuditLog` (Subject, Task Presence).
3.  **Preprocessing**: `03_preprocess_hrv.py` reads raw signals, applies artifact rejection, and outputs `hrv_metrics.csv`.
4.  **Analysis**: `04_analyze_regression.py` joins `hrv_metrics.csv` with `InteroceptionScore` (if available) to perform regression or UBDE calculation.
5.  **Output**: `data_audit.md` and regression results.

## 3. Assumptions & Constraints

*   **BIDS Compliance**: Input data is assumed to follow BIDS structure (or be convertible to it).
*   **Signal Quality**: ECG signals must have >95% valid beats for HRV calculation.
*   **Variable Independence**: Interoception scores are independent of HRV signals (different modalities).
