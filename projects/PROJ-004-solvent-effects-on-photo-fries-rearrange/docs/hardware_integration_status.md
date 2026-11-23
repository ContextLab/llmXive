# Hardware Integration Status

## Overview

This document explicitly records the current status of hardware integration for the
transient-absorption spectroscopy pipeline in the Solvent Effects on Photo-Fries
Rearrangement project (PROJ-004).

## Current Implementation State

### Capture Capability: DEFERRED

The real-time "capture" functionality for transient-absorption data acquisition
from physical instrumentation is **deferred to a future phase** pending hardware
availability and integration testing.

The module `code/hardware/interface.py` defines the API contract for hardware
interaction (see `capture_trace()`), but it does **not** perform live data
acquisition in the current deployment. When invoked in an environment without
connected hardware, the interface raises a `HardwareNotConnectedError` to
prevent silent fallback to synthetic data unless explicitly configured for CI
mode.

### Current Data Sources

The pipeline currently supports two data ingestion modes:

1. **File Ingestion (Primary)**
 - Real experimental data is ingested from user-provided CSV files via
 `code/data/ingest.py`.
 - Path: `data/raw/real_traces.csv` (or user-specified path).
 - Constraint: If `USE_REAL_DATA=true` and the file is missing, the system
 aborts with `CRITICAL: Real data file missing. Aborting.` and exits with
 code 1.

2. **Synthetic Generation (CI/Fallback Only)**
 - Deterministic synthetic traces are generated via `code/data/generate_synthetic.py`
 **only** when `USE_REAL_DATA` is false or unset.
 - Output: `data/raw/synthetic_traces.csv`.
 - Constraint: This mode is strictly for CI logic testing and model validation.
 It is **not** authorized as a primary research data source.

## Hardware Requirements (Future Phase)

When hardware integration is pursued, the following specifications are required:

- **Instrument**: Transient Absorption Spectrometer (e.g., Edinburgh Instruments
 LP-series or equivalent).
- **Interface**: Serial communication (RS-232 or USB-to-Serial) for data transfer.
- **Protocol**: Custom command set for trigger synchronization and data streaming.
- **Environment**: Controlled temperature (25 ± 0.5°C) and humidity (±2% RH).

## API Contract

The following API contract is defined in `code/hardware/interface.py` for future
implementation:

```python
def capture_trace(serial_port: str, timeout: float) -> Dict[str, Any]:
 """
 Captures a transient-absorption trace from the connected hardware.

 Raises:
 HardwareNotConnectedError: If the serial port cannot be initialized
 or the hardware is not detected.
 """
...
```

## Compliance with Research Integrity

This documentation satisfies the requirement to transparently report the
absence of live hardware integration while maintaining a functional pipeline
for data analysis using real file-based inputs or validated synthetic
placeholders for CI purposes.

**Note**: All research conclusions drawn from this pipeline must be based on
real experimental data ingested via file ingestion (Mode 1). Synthetic data
(Mode 2) is strictly for software validation and must not be used for
scientific claims.

## Status Summary

| Feature | Status | Notes |
|--------------------------|-------------|--------------------------------------------|
| Live Data Capture | DEFERRED | Hardware integration pending |
| File Ingestion | ACTIVE | Primary research data source |
| Synthetic Generation | ACTIVE | CI/Fallback only (not for research claims) |
| Hardware Interface API | DEFINED | Contract established, implementation pending |

## Next Steps

1. Secure access to a transient-absorption spectrometer.
2. Develop and test the serial communication protocol.
3. Implement `capture_trace()` with robust error handling.
4. Validate data integrity against known standards.
5. Update this document to reflect "ACTIVE" status for live capture.

---
*Document generated as part of Task T015d: Hardware Integration Gap Documentation.*