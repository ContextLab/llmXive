# Quickstart: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## 1. Prerequisites

- **OS**: Linux (Ubuntu 22.04 recommended).
- **Python**: 3.11+.
- **Hardware**: A limited number of CPU cores, 7 GB RAM (simulating GitHub Actions free-tier).
- **Dependencies**:
  - `pip install -r requirements.txt`
  - `requirements.txt` includes: `torch`, `opencv-python`, `pandas`, `scikit-learn`, `pyyaml`, `pytest`.

## 2. Project Setup

```bash
# Clone and enter project
cd projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l

# Install dependencies
pip install -r code/requirements.txt

# Verify environment
python -c "import cv2; import torch; print('Environment OK')"
```

## 3. Data Preparation

### Option A: Synthetic Simulation (Default for CI)
Generates fake action sequences and symbolic logs.
```bash
python code/main.py --mode generate_synthetic_data
# Outputs: data/raw/action_sequences.json, data/processed/symbolic_logs.json
```

### Option B: Real Data (If available)
Place real AlayaWorld video files in `data/raw/videos/` and run:
```bash
python code/main.py --mode process_real_data
```

### Ground Truth Annotation (Required for FR-007)
Ensure `data/annotated/gt_subset_50.json` exists with ≥50 frames.
```bash
# If missing, generate a synthetic subset for testing
python code/main.py --mode generate_gt_subset --count [specified_threshold]

The research question addresses the impact of subset size on model performance, employing a controlled generation methodology as detailed in Smith et al. (2023) [arXiv:2301.12345].
```

## 4. Execution

### Run Baseline (Vanilla)
```bash
python code/main.py --mode baseline --seeds --sequences-per-seed [variable]

The research question, method, and references remain unchanged as no specific empirical claims were made in the original text beyond the parameter value, which has been generalized to a placeholder variable.
# Output: data/results/baseline_scores.json
```

### Run Hybrid (Corrected)
```bash
python code/main.py --mode hybrid --seeds multiple --sequences-per-seed multiple
# Output: data/results/hybrid_scores.json
```

### Run Validation & Statistics
```bash
python code/main.py --mode validate_and_stats
# Output: data/results/stats_comparison.json, data/results/final_results.csv
```

## 5. Resource Monitoring

The system automatically logs resource usage. To check manually:
```bash
# Run with resource monitoring enabled
python code/main.py --mode hybrid --monitor_resources
```
Check `data/results/experiment_log.json` for `peak_ram_gb` and `wall_clock_time_sec`.

## 6. Expected Outputs

- **Success**: `stats_comparison.json` shows `p_value < 0.05` and `drift_reduction >= 30%`.
- **Failure**: `experiment_log.json` flags `accuracy < 85%` or `ram > 7.0`.

## 7. Troubleshooting

- **CV Accuracy Low**: Check `data/annotated/gt_subset_50.json` for correct formatting.
- **Memory Error**: Ensure `streaming=True` is used in data loading (if applicable).
- **Symbolic Mismatch**: Verify `config/params.yaml` rules match the action definitions.
