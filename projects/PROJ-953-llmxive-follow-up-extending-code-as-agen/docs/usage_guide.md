# Usage Guide

This document explains how to explore the artifacts produced by the pipeline
and how to interpret the key results.

## Inspecting `ground_truth.csv`

The file `data/processed/ground_truth.csv` contains one row per sampled task:

| Column | Description |
|----------------------------|-------------------------------------------------------|
| `task_id` | Unique identifier for the task |
| `code_diff` | The code modification (diff) |
| `status` | `"Parsed"` or `"Unparseable"` |
| `dynamic_execution_outcome`| `"Pass"`, `"Fail"` or `"Timeout/Fail"` |

You can open the CSV with any spreadsheet program or view it in Python:

```python
import pandas as pd
df = pd.read_csv('data/processed/ground_truth.csv')
print(df.head())
```

## Visualising a Dependency Graph

Each parsed task has a JSON graph stored under `data/graphs/<task_id>.json`.
The graph follows a simple node/edge schema and can be visualised with
**NetworkX** and **Matplotlib**:

```python
import json
import networkx as nx
import matplotlib.pyplot as plt

task_id = 'swe_bench_001' # replace with an actual ID
path = f'data/graphs/{task_id}.json'
with open(path) as f:
 data = json.load(f)

G = nx.DiGraph()
for node in data['nodes']:
 G.add_node(node['id'], type=node['type'])
for edge in data['edges']:
 G.add_edge(edge['from'], edge['to'])

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', arrows=True)
plt.title(f'Dependency Graph for {task_id}')
plt.show()
```

The `metadata` field indicates whether semantic nodes were present. If
`metadata["fallback_active"]` is `true`, the pipeline used the fallback
metrics (lines of code) for that task.

## Interpreting `threshold_sweep.json`

This file records the false‑negative rate (FNR) for each decision threshold
evaluated during sensitivity analysis. Example entry:

```json
{
 "threshold": 0.05,
 "fnr": 0.0008,
 "fp": 12,
 "fn": 0
}
```

- **threshold** – Probability cutoff for classifying a task as “needs
 dynamic execution”.
- **fnr** – Fraction of unsafe tasks incorrectly classified as safe.
- **fp** – Number of safe tasks unnecessarily flagged for dynamic execution.
- **fn** – Number of unsafe tasks missed (should be zero for a safe model).

The pipeline selects the threshold with the lowest FNR that satisfies the
safety constraint `FNR ≤ 0.001`. If no threshold meets this, the report marks
the model as unsafe.

## Interpreting `model_report.json`

The report aggregates model performance, correlation analysis, and safety
status. Key fields:

- `model_comparison` – Metrics (`f1`, `recall`, `fnr`) for Logistic Regression
 and Random Forest.
- `sensitivity_analysis` – Results of the threshold sweep (minimum achievable
 FNR, optimal threshold, safety flag).
- `correlation_coefficient` – Pearson correlation between each structural
 feature and the binary target (`dynamic_execution_needed`).
- `framing` – Must be `"associational"` per FR‑006.
- `safety_status` – `"SAFE"` if the chosen threshold respects the FNR bound,
 otherwise `"UNSAFE"`.

You can load and inspect the JSON in Python:

```python
import json
with open('data/processed/model_report.json') as f:
 report = json.load(f)
print(json.dumps(report, indent=2))
```

The correlation values help you understand which metrics are most predictive.
Positive correlation indicates higher metric values increase the likelihood of
a failure in dynamic execution.

## Frequently Asked Questions

**Q: My `ground_truth.csv` contains many `Unparseable` rows. What should I do?**
A: Unparseable tasks are excluded from feature extraction because static
analysis cannot be applied. Consider increasing the sample size or adjusting
the parsing heuristics in `extract_features.py`.

**Q: How can I change the feature set used for training?**
A: Edit `train_model.py` – modify `feature_cols` near line 110 to add or
remove column names present in `features.csv`.

**Q: I want to visualise all graphs at once.**
A: Loop over the files in `data/graphs/` and plot each with NetworkX; you may
also export them to GraphViz (`dot` format) for batch rendering.
