# Operation Logs

All pipeline operations are logged via `code/reproducibility/logs.py`. The log file `logs/operation_log.jsonl` contains entries with the following fields:

- `timestamp`
- `operation`
- `input_file`
- `output_file`
- `parameters`
- `status`
- `duration_ms`

Sample entry:
```json
{
 "timestamp": "2026-06-17T12:34:56.789Z",
 "operation": "download_knot_atlas",
 "input_file": null,
 "output_file": "data/raw/knot_atlas_raw.json",
 "parameters": {"retry_max": 5},
 "status": "success",
 "duration_ms": 842
}
```
