# Utils Module

This directory contains utility modules for the llmXive automated science pipeline.

## Modules

- `logging_utils.py`: Logging infrastructure for exclusion tracking and warnings.

## Usage

```python
from utils.logging_utils import log_exclusion, init_exclusion_log

# Initialize the log (if not already done)
init_exclusion_log()

# Log an exclusion
log_exclusion(
 dataset_id="adult_dataset",
 missing_variable_name="age",
 reason="Age variable not found in raw CSV file"
)
```

## Exclusion Log Format

The exclusion log (`logs/exclusion.log`) is a CSV file with the following columns:

- `timestamp`: ISO 8601 formatted timestamp of the exclusion event.
- `dataset_id`: Unique identifier for the dataset.
- `missing_variable_name`: Name of the missing variable.
- `reason`: Explanation of why the exclusion occurred.

## FR-008 Compliance

All logging messages include the associational disclaimer:
"Findings are associational only; no causal claims are made."
