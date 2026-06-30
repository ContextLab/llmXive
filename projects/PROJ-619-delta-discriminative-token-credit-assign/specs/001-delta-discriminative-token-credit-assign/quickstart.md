# DelTA CPU Proxy: Quick Start

This guide runs the simplified, CPU-tractable reproduction of the DelTA paper's core mechanism.

### Prerequisites
Ensure you have Python 3.8+ and the following packages installed:
```bash
pip install numpy pandas matplotlib
```

### Execution
Run the simulation script. It will generate synthetic data, apply the Standard RLVR and DelTA logic, and save artifacts.

```bash
python code/delta_proxy.py
```

### Verification
After execution, verify the outputs:
1.  **Numeric Results**: Check `data/centroids_comparison.csv` for the cosine similarity scores. The DelTA score should indicate better separation (more negative cosine similarity) than Standard RLVR.
2.  **Visualization**: Open `figures/separation_analysis.png` to see the projected centroids.
