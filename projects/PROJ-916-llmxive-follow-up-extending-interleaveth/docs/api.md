# API Reference

## Modules

### `src/simulator`
- `parser.py`: Converts text captions into structured JSON scene descriptions.
- `noise_injector.py`: Injects semantic noise to simulate grounding gaps.
- `simulator.py`: Orchestrates Perfect/Noisy mode switching.
- `validator.py`: Detects ambiguous spatial relationships.

### `src/agents`
- `planner.py`: Generates intent and next steps.
- `generator.py`: Reconstructs `SceneDescription` JSON using an LLM.
- `critic.py`: Evaluates generated JSON against prompts and ground truth.
- `interfaces.py`: Defines input/output contracts for agents.

### `src/pipeline`
- `orchestrator.py`: Manages the agentic loop (Planner → Generator → Critic).
- `logger.py`: Logs `TrajectoryLog` states and critiques.

### `src/stats`
- `simulator_metrics.py`: Calculates `simulator_error_rate` and verifies noise bounds.
- `generator_metrics.py`: Calculates "Generator Error Rate".
- `reasoning_score.py`: Computes F1-score or Graph Edit Distance.
- `analyzer.py`: Performs statistical tests (t-test, Wilcoxon) and effect size calculations.
- `report_generator.py`: Generates `statistical_significance_report.md`.

### `src/data`
- `loader.py`: Streams Visual Genome, GQA, WISE, and RISE datasets.

### `src/utils`
- `logging.py`: Tracks RAM usage and execution time.
- `checksum.py`: Verifies downloaded dataset shards.
- `parser.py`: Common parsing logic.

## Configuration

- `src/config.py`: Environment configuration (seeds, thresholds, batch sizes).

## Entry Points

- `run_experiment.py`: Main entry point for executing the full pipeline.
