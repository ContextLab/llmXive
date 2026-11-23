# Configuration Guide

This document explains how to configure the pipeline parameters.

## `code/config.yaml`

The central configuration file for the pipeline.

```yaml
pipeline:
 name: "MMN_Predictive_Coding_Analysis"
 version: "1.0.0"

data:
 raw_dir: "data/raw"
 processed_dir: "data/processed"
 results_dir: "results"

preprocessing:
 filter:
 lowcut: 1.0
 highcut: 30.0
 l_trans_bandwidth: "auto"
 h_trans_bandwidth: "auto"
 montage:
 type: "standard_32"
 channels: ["Fz", "FCz", "Cz", "Pz", "F3", "F4", "C3", "C4", "P3", "P4", "F7", "F8", "T7", "T8", "P7", "P8", "O1", "O2"]
 epoch:
 tmin: -0.2
 tmax: 0.6
 baseline: [-0.2, 0.0]
 ica:
 method: "fastica"
 threshold: 0.8
 max_components: 20

extraction:
 peak_window:
 start: 0.15
 end: 0.25
 snr_window:
 start: -0.2
 end: 0.0

statistics:
 fdr_method: "fdr_bh"
 permutation_tests: 1000
 cluster_threshold: 0.05

logging:
 level: "INFO"
 file: "code/logs/pipeline.log"
```

## Environment Variables

- `OPENNEURO_API_KEY`: Optional. Required only for private datasets.
- `PROJECT_ROOT`: Optional. Overrides the default project root detection.

## Modifying Parameters

To change the filter range or epoch window, edit `code/config.yaml` and re-run the pipeline. No code changes are required for parameter adjustments.

## Validation

The pipeline validates the configuration at startup. If a parameter is missing or invalid, the script will exit with an error message indicating the issue.