# Data Model: ArcANE

## Entities

### Character
- `name`: str
- `source_text_id`: str (Gutenberg ID)

### Axis
- `character`: str
- `type`: "coarse" | "fine"
- `name`: str
- `description`: str
- `source_observation`: str (for Fine only)

### Probe
- `character`: str
- `scenario`: str
- `axes`: List[str] (references to Axis IDs)
- `similarity_score`: float (vs source text)

### Response
- `probe_id`: str
- `model_response`: str
- `judge_score`: float
- `rule_score`: float
- `consistency_score`: float

## Storage Formats

- **Axes**: `data/derived/axes.jsonl`
- **Probes**: `data/derived/probes.jsonl`
- **Results**: `data/derived/results_raw.jsonl`, `data/derived/results_final.jsonl`
- **Gold Standard**: `data/gold_standard/human_annotations.json`
