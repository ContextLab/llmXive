# Data Model

## Entities

### RolloutLog
- `task_id`: str
- `cycle`: int
- `student_confidence`: float
- `expert_confidence`: float
- `prompt_length`: int
- `correct`: bool

### RunMetadata
- `seed`: int
- `timestamp`: datetime
- `config_hash`: str
- `mode`: str (baseline | cap)

### AggregatedMetrics
- `task_id`: str
- `seed`: int
- `aucc`: float
- `final_accuracy`: float
- `prompt_length_avg`: float
- `run_mode`: str

### ConvergenceResult
- `cycle`: int
- `accuracy`: float
- `prompt_content`: str (hash)

### StateStore
- `project_id`: str
- `history`: List[CycleRecord]
 - `cycle`: int
 - `confidence_mean`: float
 - `confidence_var`: float
 - `classification`: str (rejected | fluctuating | accepted)
