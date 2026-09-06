# Architecture Specification: Dream-State Learning

## 1. System Components

### 1.1 Data Pipeline (`code/data/`)
- **Loader**: Handles downloading and verification of GLUE/SuperGLUE datasets.
 - *Constraint*: Must abort on checksum mismatch (`DataIntegrityError`).
 - *Source*: HuggingFace `datasets` library.
- **Augment**: Implements Denoising Autoencoder (DAE) masking.
 - *Mechanism*: Random token masking consistent with BERT pre-training objectives.
 - *Rate*: Moderate mask rate (configurable, default ~15-30%).

### 1.2 Model Core (`code/models/`)
- **Trainer**: Orchestrates the alternating Wake/Dream loop.
 - *Wake Phase*: Standard Cross-Entropy loss on real data.
 - *Dream Phase*: DAE loss (reconstruction of masked tokens).
 - *Scheduler*: `DreamScheduler` enforces the 4:1 Wake/Dream ratio.
 - *Warm-up*: Skips Dream phase for the first N steps (default 10) to ensure initial stability.
 - *Entropy Check*: Monitors output entropy. If < 0.5 bits, triggers up to 3 retries or discards the batch.
- **Memory Monitor**: Integrated into the training loop to track peak RSS.
 - *Action*: On OOM, saves checkpoint and aborts execution.

### 1.3 Evaluation & Analysis (`code/eval/`)
- **Metrics**: Calculates few-shot accuracy and performs statistical tests.
 - *Test*: Wilcoxon signed-rank test (`scipy.stats.wilcoxon`).
- **Reporting**: Generates JSON reports for:
 - Comparative performance (Experimental vs. Baseline).
 - Sensitivity analysis (Temperature sweep variance).
- **Statistical Analysis**: Aggregates results from multiple seeds (default 5) to compute p-values.

### 1.4 Orchestration (`code/main.py`)
- **Modes**:
 - `single_seed`: Run one experiment.
 - `full_comparison`: Run 5 seeds for both experimental and baseline, then compare.
 - `temperature_sweep`: Grid search over {0.5, 0.7, 0.9}.
- **Resource Enforcement**:
 - Time limit monitoring (abort if > 5 hours).
 - Memory limit enforcement (via `MemoryMonitor`).

## 2. Data Flow

1. **Initialization**: `main.py` loads config, sets seeds, and initializes `Trainer`.
2. **Data Loading**: `loader.py` fetches real GLUE data with checksum verification.
3. **Training Loop**:
 - **Wake**: `Trainer` processes real batch -> CE Loss -> Update.
 - **Dream**: `Trainer` applies DAE mask -> Reconstruction Loss -> Update.
 - **Checks**: Entropy validation, memory monitoring, warm-up logic.
4. **Evaluation**: After training, `eval/metrics.py` computes accuracy on held-out data.
5. **Aggregation**: `scripts/generate_final_report.py` combines results from multiple seeds.
6. **Reporting**: `eval/reporting.py` and `sensitivity_report.py` generate final JSON artifacts.

## 3. Failure Modes & Recovery

- **Data Corruption**: `DataIntegrityError` raised immediately. No synthetic fallback.
- **OOM**: `MemoryLimitExceeded` raised by `MemoryMonitor`. Checkpoint saved, process exits.
- **Time Limit**: `TimeLimitExceeded` raised by `main.py`. Process exits gracefully.
- **Low Entropy**: Batch discarded or retried locally (max 3 attempts).

## 4. Configuration

All hyperparameters are defined in `code/config.py`:
- `MAX_WALL_CLOCK_HOURS`: Default 5.
- `MEMORY_LIMIT_GB`: Default 6.
- `DREAM_RATIO`: Default 4 (Wake: 4, Dream: 1).
- `WARMUP_STEPS`: Default 10.
- `ENTROPY_THRESHOLD`: Default 0.5 bits.
- `TEMPERATURES`: {0.5, 0.7, 0.9} for sensitivity analysis.
