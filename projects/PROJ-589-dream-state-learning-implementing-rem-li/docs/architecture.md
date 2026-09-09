# Architecture Overview: Dream-State Learning

## System Design

The Dream-State Learning system implements a biologically-inspired training paradigm
that alternates between two distinct phases:

### 1. Wake Phase (Supervised Fine-Tuning)

During the wake phase, the model performs standard supervised learning on real
GLUE/SuperGLUE data:

- **Input**: Raw text sequences from the dataset
- **Objective**: Minimize cross-entropy loss for next-token prediction
- **Optimizer**: AdamW with configurable learning rate
- **Batching**: PyTorch DataLoader with batch size from config

This phase corresponds to "awake" learning in biological systems, where new
information is acquired from the environment.

### 2. Dream Phase (Denoising Autoencoder)

During the dream phase, the model performs reconstruction learning on masked
versions of real data:

- **Input**: Real data with 15% of tokens randomly masked (BERT-style)
- **Objective**: Reconstruct the original tokens from masked input
- **Loss**: Cross-entropy between predicted and original tokens
- **Ratio**: 5 wake steps per 1 dream step (configurable)

This phase mimics REM sleep consolidation, where the brain replays and
strengthens memories without new external input.

## Key Components

### Data Pipeline (`code/data/`)

- **`loader.py`**: Downloads and verifies GLUE/SuperGLUE datasets
 - SHA-256 checksum verification
 - Automatic download on first run
 - Caching in `data/raw/`

- **`augment.py`**: Implements DAE masking strategy
 - `MASK_RATE = 0.15` (15% masking)
 - Random token selection
 - Consistent with BERT preprocessing

### Training Engine (`code/models/trainer.py`)

The `Trainer` class orchestrates the wake/dream cycle:

- **`DreamScheduler`**: Manages wake-to-dream ratio
 - Tracks step count
 - Triggers dream phase at modulo intervals
 - Enforces warm-up period (no dream before step 10)

- **`Trainer`**: Core training loop
 - Alternates between wake and dream phases
 - Computes entropy metrics
 - Handles low-entropy retry logic
 - Integrates memory monitoring

### Evaluation (`code/eval/`)

- **`metrics.py`**: Accuracy and performance metrics
 - Few-shot accuracy calculation
 - Holdout evaluation

- **`statistical_analysis.py`**: Comparative analysis
 - Paired t-test (scipy.stats.ttest_rel)
 - Accuracy difference computation
 - Significance testing (α=0.05)

- **`sensitivity_report.py`**: Hyperparameter analysis
 - Temperature sweep execution
 - Variance computation
 - Report generation

### Utilities (`code/utils/`)

- **`logger.py`**: Structured JSON logging
 - File and stdout output
 - Event-based logging (phase transitions, entropy metrics)

- **`memory_monitor.py`**: Memory tracking and enforcement
 - Peak RSS tracking via /proc/self/status
 - Hard abort on OOM
 - Checkpoint saving before termination

- **`exceptions.py`**: Custom exception classes
 - `DataIntegrityError`: Dataset verification failures
 - `TimeLimitExceeded`: Wall-clock limit violations
 - `MemoryLimitExceeded`: RAM limit violations

## Workflow

```
1. Initialization
 ├─ Load configuration (config.py)
 ├─ Verify directory structure
 └─ Download datasets (if not cached)

2. Training Loop (per seed)
 ├─ Initialize model and optimizer
 ├─ For each step:
 │ ├─ Wake Phase (standard SFT)
 │ │ ├─ Load batch
 │ │ ├─ Compute loss
 │ │ └─ Update weights
 │ ├─ Dream Phase (every 5 steps after warm-up)
 │ │ ├─ Apply 15% masking
 │ │ ├─ Compute reconstruction loss
 │ │ └─ Update weights
 │ └─ Entropy Check
 │ ├─ Calculate average entropy
 │ ├─ If < 0.5 bits/token: retry or discard
 │ └─ Log metrics
 └─ Save checkpoint

3. Evaluation
 ├─ Run on held-out data
 ├─ Compute accuracy metrics
 └─ Save results

4. Analysis
 ├─ Compare experimental vs. baseline
 ├─ Run paired t-test
 └─ Generate reports

5. Sensitivity Analysis (optional)
 ├─ Sweep temperature hyperparameters
 ├─ Re-initialize for each run
 └─ Compute variance metrics
```

## Data Flow

```
GLUE/SuperGLUE
 ↓
code/data/loader.py (download + verify)
 ↓
data/raw/ (cached datasets)
 ↓
code/data/augment.py (masking for dream phase)
 ↓
code/models/trainer.py (training loop)
 ↓
code/eval/metrics.py (accuracy computation)
 ↓
data/results/ (reports and checkpoints)
```

## Configuration

All hyperparameters are centralized in `code/config.py`:

```python
MASK_RATE = 0.15 # Dream phase masking probability
WARMUP_STEPS = 10 # Minimum steps before dream phase
DREAM_RATIO = 5 # Wake steps per dream step
ENTROPY_THRESHOLD = 0.5 # Low-entropy detection (bits/token)
MAX_WALL_CLOCK_HOURS = 5.5 # Runtime limit
MEMORY_LIMIT_GB = 8 # RAM limit
```

## Logging and Monitoring

The system uses structured JSON logging for all events:

- **Phase Transitions**: Wake → Dream, Dream → Wake
- **Entropy Metrics**: Per-batch entropy values
- **Warm-up Status**: Steps remaining until dream phase enabled
- **Memory Usage**: Peak RSS tracking
- **Errors**: Stack traces and context

Logs are saved to `data/logs/` with timestamps.

## Constraints and Limitations

### Resource Constraints
- **CPU-only**: No GPU support for CI compatibility
- **Memory**: 8GB RAM limit (enforced by memory_monitor)
- **Time**: 5.5 hour wall-clock limit (enforced by main.py)
- **Disk**: ~14GB for datasets and checkpoints

### Data Constraints
- Only small GLUE/SuperGLUE subsets (e.g., MRPC, RTE)
- Real data only (no synthetic generation)
- SHA-256 checksum verification required

### Architectural Notes
- Dream phase uses DAE on masked real data (not generative replay)
- This diverges from spec.md FR-002 but follows plan.md "Critical Revision"
- Spec amendment pending to align documentation with implementation

## Error Handling

The system implements fail-fast error handling:

- **Data Integrity**: RuntimeError on checksum mismatch
- **Memory OOM**: Hard abort with checkpoint save
- **Time Limit**: TimeLimitExceeded exception
- **Low Entropy**: Retry (up to 3x) or discard batch

All errors are logged with full context for debugging.

## Future Work

- Extend to larger datasets via streaming
- Implement true generative replay (pending spec amendment)
- Add GPU support for local development
- Explore alternative consolidation mechanisms