# Quick Start: Dynamic Socio-Cognitive State Injection

This guide walks you through setting up and running the llmXive pipeline for dynamic state injection experiments.

## Prerequisites

- Python 3.11+
- 16GB+ RAM (for model loading and data processing)
- No GPU required (CPU-only execution enforced)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd llmXive
pip install -r requirements.txt
```

**Note**: `requirements.txt` explicitly excludes GPU-accelerated libraries (`bitsandbytes`, `flash-attn`) to comply with FR-004.

## 2. Verify Project Structure

Run the setup script to ensure all directories exist:

```bash
python code/setup_structure.py
```

This creates:
- `code/`, `data/raw/`, `data/processed/`, `data/results/`
- `tests/`, `contracts/`

## 3. Generate Conflict Trajectories (US1)

Generate synthetic conflict dialogues with targeted oversampling:

```bash
python code/data/generator.py
```

**Outputs**:
- `data/processed/trajectories.json`: Full conflict trajectories
- `data/processed/generation_stats.json`: Distribution statistics (verifies >40% target categories)
- `data/processed/classifier_training_data.json`: Turn-level training pairs

**Validation**: Check `generation_stats.json` to ensure the oversampling threshold is met.

## 4. Train State Classifier (US2)

Train the lightweight logistic regression classifier on the generated data:

```bash
python code/models/classifier.py
```

**Outputs**:
- `data/processed/classifier.pkl`: Trained model artifact

**Note**: The classifier uses TF-IDF features on `turn_text` to predict socio-cognitive states.

## 5. Run Experiments (US2)

Execute the paired mediation experiment (Adapter vs. Static) on all trajectories:

```bash
python code/experiments/runner.py
```

**Flags**:
- `--seed <int>`: Ensure deterministic execution (default: 42)
- `--models <list>`: Specify which LLMs to run (default: all available within memory limits)

**Outputs**:
- `data/processed/experiment_logs.json`: Per-turn logs with `confidence_score` and `injected_state`
- `data/results/perf_report.json`: Throughput and latency metrics

**Constraints**:
- The script enforces CPU-only execution (`torch.cuda.is_available()` check).
- Models exceeding 7GB RAM are automatically skipped (see T009).

## 6. Analyze Results (US3)

Compute consensus gap closure and statistical significance:

```bash
python code/analysis/stats.py
```

**Outputs**:
- `data/results/statistical_report.json`: T-statistic, p-value, Cohen's d, significance flags
- `data/results/sensitivity_analysis_report.json`: Confidence threshold sensitivity analysis

**Stratified Analysis**:
The report includes a `stratified_results` section comparing the full dataset against the "high-difficulty" subset (high emotional reactivity or diverse cultural identity).

## 7. Performance Validation

Check performance metrics:

```bash
python code/analysis/perf_monitor.py
```

**Thresholds**:
- Throughput: > 40 trajectories/hour
- Latency: < 45 seconds/trajectory

If thresholds are violated, the CI build fails (see `scripts/check_perf.sh`).

## 8. Memory Profiling

Run the memory profiler to ensure no model exceeds RAM limits:

```bash
python code/analysis/memory_profiler.py
```

**Output**: `data/results/memory_profile_report.json`

**Failure Condition**: If any model exceeds the RAM threshold, the build fails.

## Troubleshooting

### CUDA Detected
If you see `CUDA device detected`, ensure you are running on a CPU-only environment. The script explicitly fails if `torch.cuda.is_available()` is True.

### Model Too Large
If a model is skipped due to memory limits, check `code/experiments/model_loader.py` logs. You can adjust the 7GB threshold in `config.py` if necessary (not recommended).

### Missing Data Files
Ensure you run tasks in order:
1. `generator.py` (US1)
2. `classifier.py` (US2)
3. `runner.py` (US2)
4. `stats.py` (US3)

## Reproducibility

To reproduce results exactly:
1. Use the same `--seed` in `runner.py`.
2. Use the same subset of LLMs.
3. Ensure the same `trajectories.json` is used as input.

Statistical reproducibility is verified by ensuring the mean consensus gap variance between runs is < `config.STATISTICAL_VARIANCE_TOLERANCE`.