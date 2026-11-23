# API Reference

*Generated on: 2024-01-01 12:00:00*

This document provides a comprehensive reference for the Python analysis scripts
used in the cache line padding impact study.

---

## Analysis Module (`code/analysis/`)

Core analysis and statistical processing utilities.

## `benchmark_contracts.py`

Pydantic schema definitions for data validation.

### Imports
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
```

### Classes
### `AggregatedResult`

Schema for aggregated benchmark results per thread count and configuration.

**Bases:** `BaseModel`

**Methods:**
- `model_validate`
- `model_dump`
- `model_dump_json`

*Defined at line 10*

### `BenchmarkRun`

Schema for a single benchmark run record.

**Bases:** `BaseModel`

**Methods:**
- `model_validate`
- `model_dump`
- `model_dump_json`

*Defined at line 25*

### `StatisticalComparison`

Schema for statistical comparison results between packed and padded configurations.

**Bases:** `BaseModel`

**Methods:**
- `model_validate`
- `model_dump`
- `model_dump_json`

*Defined at line 40*

---

## `hardware_detect.py`

Hardware detection and configuration utilities for benchmark execution.

### Imports
```python
import os
import subprocess
import sys
import yaml
from pathlib import Path
```

### Functions
### `generate_hardware_spec`

Detects hardware characteristics and generates a YAML specification file.

**Parameters:**
- `output_path`

*Defined at line 20*

### `get_cache_line_size`

Detects the CPU cache line size from /sys or defaults to 64 bytes.

**Returns:** `int`

*Defined at line 35*

### `get_core_count`

Returns the number of logical CPU cores available.

**Returns:** `int`

*Defined at line 15*

### `main`

Entry point for hardware specification generation script.

*Defined at line 60*

### `set_cpu_governor`

Sets the CPU frequency governor to 'performance' mode.

**Parameters:**
- `governor`

*Defined at line 45*

---

## `process_timeout_data.py`

Utility for processing benchmark results that encountered timeouts.

### Imports
```python
import pandas as pd
import sys
from pathlib import Path
import json
```

### Functions
### `main`

Entry point for timeout data processing script.

*Defined at line 30*

### `process_benchmark_results`

Processes benchmark results CSV, handling timeout entries appropriately.

**Parameters:**
- `input_path`
- `output_path`

*Defined at line 10*

---

## `run_analysis.py`

Main analysis script for statistical comparison and visualization.

### Imports
```python
import os
import sys
import glob
from pathlib import Path
import pandas as pd
import numpy as np
```

### Functions
### `aggregate_results`

Aggregates raw benchmark data by thread count and configuration.

**Parameters:**
- `data`
- `groupby_cols`

**Returns:** `DataFrame`

*Defined at line 45*

### `benjamini_hochberg`

Applies the Benjamini-Hochberg procedure for False Discovery Rate correction.

**Parameters:**
- `p_values`

**Returns:** `List[float]`

*Defined at line 85*

### `calculate_cohens_d`

Calculates Cohen's d effect size for two samples.

**Parameters:**
- `group1`
- `group2`

**Returns:** `float`

*Defined at line 65*

### `calculate_throughput`

Calculates throughput (increments per second) from timing data.

**Parameters:**
- `iterations`
- `time_ms`

**Returns:** `float`

*Defined at line 25*

### `generate_plot`

Generates a line plot with confidence intervals for throughput comparison.

**Parameters:**
- `data`
- `output_path`

*Defined at line 110*

### `load_benchmark_data`

Loads and validates benchmark data from CSV files.

**Parameters:**
- `input_pattern`

**Returns:** `DataFrame`

*Defined at line 10*

### `main`

Entry point for the analysis pipeline.

*Defined at line 140*

### `perform_statistical_tests`

Performs t-tests and calculates effect sizes for each thread count.

**Parameters:**
- `aggregated_data`

**Returns:** `DataFrame`

*Defined at line 100*

---

## `update_checksums.py`

Utility for generating and updating SHA-256 checksums of artifacts.

### Imports
```python
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
```

### Functions
### `calculate_sha256`

Calculates the SHA-256 hash of a file.

**Parameters:**
- `file_path`

**Returns:** `str`

*Defined at line 10*

### `main`

Entry point for checksum update script.

*Defined at line 50*

### `update_checksums`

Updates the checksums.json file with new artifact hashes.

**Parameters:**
- `artifacts_dir`
- `output_path`

*Defined at line 25*

---

## `verify_results.py`

Verification script to validate benchmark results against expectations.

### Imports
```python
import os
import sys
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
```

### Functions
### `aggregate_results`

Aggregates benchmark data for verification.

**Parameters:**
- `data`

**Returns:** `DataFrame`

*Defined at line 35*

### `calculate_throughput`

Calculates throughput for verification.

**Parameters:**
- `iterations`
- `time_ms`

**Returns:** `float`

*Defined at line 25*

### `load_benchmark_data`

Loads benchmark data for verification.

**Parameters:**
- `input_path`

**Returns:** `DataFrame`

*Defined at line 15*

### `main`

Entry point for verification script.

*Defined at line 100*

### `run_benchmark`

Executes the benchmark binary and returns output path.

**Parameters:**
- `config`
- `threads`

**Returns:** `str`

*Defined at line 10*

### `verify_padding_effect`

Verifies that padded counters outperform packed counters at high thread counts.

**Parameters:**
- `data`

**Returns:** `bool`

*Defined at line 60*

---

## `write_final_results.py`

Script to write final processed results to disk.

### Imports
```python
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
```

### Functions
### `main`

Entry point for final results writing script.

*Defined at line 40*

### `write_final_results`

Writes aggregated and analyzed results to CSV.

**Parameters:**
- `data`
- `output_path`

*Defined at line 15*

---

## Scripts Module (`code/scripts/`)

Utility scripts for environment setup and formatting.

## `format_check.py`

Script to check code formatting compliance.

### Imports
```python
import subprocess
import sys
import os
```

### Functions
### `main`

Entry point for format check script.

*Defined at line 20*

### `run_command`

Executes a shell command and returns output.

**Parameters:**
- `cmd`

**Returns:** `str`

*Defined at line 10*

---

## `setup_env.py`

Environment setup script for benchmark execution.

### Imports
```python
import sys
import os
import subprocess
import time
```

### Functions
### `main`

Entry point for environment setup script.

*Defined at line 25*