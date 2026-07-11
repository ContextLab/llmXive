# Usage Guide: Co-Evolving Policy Distillation

This document provides detailed instructions on how to run the three distinct agent training conditions implemented in the llmXive pipeline: **Sequential**, **Mixed-task**, and **Coevolving**.

## Prerequisites

Ensure you have completed the following:
1. Installed dependencies: `pip install -r requirements.txt`
2. Generated the synthetic datasets (Phase 3): `python -m src.cli generate`
3. Validated the datasets (Phase 3): `python -m src.cli validate`

If you have not generated data yet, run:
```bash
python -m src.cli generate --n-proofs 500 --n-grids 500 --seed 42
```

## Training Conditions

The pipeline supports three training paradigms. Each condition trains the agent on the same total volume of data (rule evaluations) but differs in the scheduling of task domains.

### 1. Sequential Training
The agent trains on one task domain (e.g., all Logic Proofs) until completion, then switches to the next domain (e.g., all Grid Worlds).

**Command:**
```bash
python -m src.cli train --condition sequential --config data/config.json
```

**Output:**
Results are saved to `data/results/sequential_run_<timestamp>.json`.

### 2. Mixed-task Training
The agent trains on a random mixture of task domains at every generation step. This simulates a standard multi-task learning environment.

**Command:**
```bash
python -m src.cli train --condition mixed --config data/config.json
```

**Output:**
Results are saved to `data/results/mixed_run_<timestamp>.json`.

### 3. Co-evolving Training
The agent maintains sub-populations for each task domain. At every generation step, rule-sets are exchanged bidirectionally between sub-populations, allowing for co-evolution of policies.

**Command:**
```bash
python -m src.cli train --condition coevolving --config data/config.json
```

**Output:**
Results are saved to `data/results/coevolving_run_<timestamp>.json`.

## Full Pipeline Execution

To run the complete experiment (Generation -> Validation -> Training -> Batch Analysis), use the main entry point:

```bash
python -m src.cli run --runs 30 --conditions sequential,mixed,coevolving
```

This will:
1. Generate synthetic data if missing.
2. Validate data integrity.
3. Run 30 independent batches for each condition (total 90 runs).
4. Aggregate results.
5. Perform statistical analysis (ANOVA, Tukey HSD).
6. Generate the final report in `data/results/forgetting_analysis.json`.

## Configuration

Training behavior is controlled via `data/config.json`. Key parameters include:
- `generations`: Number of evolutionary steps per run.
- `population_size`: Number of agents per sub-population (for co-evolving).
- `rule_evaluation_budget`: Total number of rule evaluations allowed (enforces parity).

## Expected Outputs

After a successful run, the `data/results/` directory will contain:
- Individual run JSONs for each condition.
- `aggregated_results.json`: Combined metrics across all runs.
- `forgetting_analysis.json`: Final statistical report including p-values and retention rates.
- `checksums.json`: Integrity hashes for all generated artifacts.
