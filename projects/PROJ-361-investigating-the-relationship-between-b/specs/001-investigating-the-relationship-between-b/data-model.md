# Data Model

## Entities

### Subject
- `subject_id`: str (e.g., "sub-01")
- `age`: int | None
- `sex`: str | None

### ConnectivityMatrix
- `subject_id`: str
- `matrix`: numpy.ndarray (T x N, where T is time points, N is ROIs)
- `roi_labels`: list[str]

### TopologyMetrics
- `subject_id`: str
- `modularity`: float
- `path_length`: float
- `clustering_coefficient`: float
- `global_efficiency`: float
- `small_worldness`: float

### IllusionScore
- `subject_id`: str
- `muller_lyer_error`: float
- `ponzo_error`: float
- `study_id`: str

## Relationships
- One Subject has one ConnectivityMatrix.
- One Subject has one TopologyMetrics.
- One Subject has one IllusionScore.
