# PROJ-962: Non-Neural Approximation of VLA Priors

## Project Goal
To implement a CPU-only pipeline that approximates Vision-Language-Action (VLA) priors using non-neural models (Decision Trees, GMMs) derived from clustered kinematic data. The system validates its performance against a VLA proxy baseline using statistical tests.

## Key Features
- **CPU-Only Execution**: Enforced via runtime checks; no GPU dependencies.
- **Adaptive Clustering**: K-means with automatic `k` reduction and HAC fallback for robust behavior grouping.
- **Sequential Model Selection**: Automatically chooses between Decision Trees and GMMs based on R² and inference time.
- **Statistical Rigor**: Paired t-tests for binary success and continuous fidelity metrics.
- **Data Integrity**: Strict "fail loudly" policy for data fetching; no synthetic fallbacks.

## Architecture
1. **Ingestion (`code/01_ingest_cluster.py`)**: Streams Qwen-VLA data, extracts kinematic features, and performs clustering.
2. **Training (`code/02_train_models.py`)**: Generates BERT embeddings and fits cluster-specific models.
3. **Inference (`code/03_inference.py`)**: Predicts trajectories for new prompts.
4. **Simulation (`code/04_simulate_eval.py`)**: Evaluates trajectories in PyBullet and runs statistical comparisons.

## Documentation
- [Quick Start Guide](docs/quickstart.md): Installation and execution instructions.
- [Research Methodology](docs/research.md): Detailed explanation of algorithms, selection criteria, and validation.

## Success Criteria
- **SC-001**: Trajectory fidelity within error margin of VLA proxy.
- **SC-002**: Random baseline comparison included.
- **SC-003**: CPU-only execution (memory < 7GB).
- **SC-004**: Paired t-tests performed.
- **SC-005**: Clustering coverage ≥ 98%.

## License
llmXive Research Initiative.
