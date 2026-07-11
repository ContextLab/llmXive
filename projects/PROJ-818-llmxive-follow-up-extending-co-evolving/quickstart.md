# Quickstart: Co-Evolving Policy Distillation

Get the llmXive pipeline running in minutes. This guide covers data generation, training the three agent conditions, and analyzing forgetting rates.

## 1. Setup

```bash
# Clone and install
pip install -e.
pip install -r requirements.txt
```

## 2. Generate Data

Create the synthetic propositional logic proofs and grid-world navigation tasks.

```bash
python -m src.cli generate \
 --n-proofs 500 \
 --n-grids 500 \
 --test-size 50 \
 --seed 42
```

This creates `data/training_proofs.json`, `data/training_grids.json`, and `data/test_instances.json`.

## 3. Validate Data

Ensure the generated data meets validity constraints before training.

```bash
python -m src.cli validate
```

*{{claim:c_293bf819}} (Wikipedia: Exit status, https://en.wikipedia.org/wiki/Exit_status) {{claim:c_47c98163}}*

## 4. Run a Single Training Condition

### Sequential
```bash
python -m src.cli train --condition sequential --generations 50
```

### Mixed-task
```bash
python -m src.cli train --condition mixed --generations 50
```

### Co-evolving
```bash
python -m src.cli train --condition coevolving --generations 50
```

## 5. Run Full Batch Experiment

To reproduce the scientific study (30+ runs per condition), execute the full pipeline:

```bash
python -m src.cli run --runs 30 --conditions sequential,mixed,coevolving
```

This command orchestrates:
1. **Generation**: Creates fresh data if needed.
2. **Validation**: Gates training on valid data.
3. **Batch Training**: Executes 30 independent runs for each of the 3 conditions.
4. **Analysis**: Computes forgetting metrics, runs Mixed-Design ANOVA, and performs Tukey HSD post-hoc tests.

## 6. View Results

The final statistical report is located at `data/results/forgetting_analysis.json`.

```json
{
 "anova_results": {
 "F_statistic": 4.52,
 "p_value": 0.003,
 "significant": true
 },
 "retention_comparison": {
 "coevolving_mean": 0.85,
 "mixed_mean": 0.72,
 "difference": 0.13,
 "p_value": 0.01
 }
}
```

## Troubleshooting

- **ParityError**: If the training fails with a parity error, ensure your `config.json` `rule_evaluation_budget` is consistent across all conditions. The system enforces exact parity.
- **Validation Failed**: If validation fails, check `data/results/validation_report.json` for specific invalid proofs or unsolvable grids. Regenerate data with a different seed.