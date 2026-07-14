# Usage Examples

## Example 1: Running the Full Pipeline

```python
from main import main

if __name__ == "__main__":
 main()
```

This single command executes:
1. Download
2. Preprocessing
3. Metrics Calculation
4. Statistical Analysis
5. Report Generation

## Example 2: Customizing Analysis

To change the frequency band for connectivity analysis:

```yaml
# code/config.yaml
frequency_bands:
 theta: [4, 8]
 alpha: [8, 13]
 beta: [13, 30] # Add custom band
```

Then, modify `metrics.py` to use the new band in `compute_waking_connectivity`.

## Example 3: Debugging Preprocessing

To inspect intermediate results:

```python
from preprocess import main as preprocess_main
from loaders import load_subject_data

# Run preprocessing
preprocess_main()

# Load and inspect a specific subject
raw, events = load_subject_data("data/processed/STUDY_001.npz")
print(f"Epoch shape: {raw.shape}")
```

## Example 4: Visualizing Results (Manual)

Although the pipeline outputs JSON/Markdown, you can visualize results using Python:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/metrics/SubjectMetrics.csv")

plt.scatter(df['degree_centrality'], df['pli_n2'])
plt.xlabel("Degree Centrality")
plt.ylabel("PLI (N2)")
plt.title("Centrality vs. Synchrony")
plt.savefig("figures/centrality_vs_synchrony.png")
```
