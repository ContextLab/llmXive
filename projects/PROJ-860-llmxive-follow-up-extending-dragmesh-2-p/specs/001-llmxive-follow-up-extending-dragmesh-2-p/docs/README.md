# Virtual Tactile Zero‑Shot Adaptation

This repository implements the **Virtual Tactile** research pipeline described in the feature specification `001-virtual-tactile-adaptation`. It provides a CPU‑only end‑to‑end experiment that:

1. Generates novel articulated objects with **unseen friction** coefficients.  
2. Estimates a **Dynamic Resistance Proxy** (`k_norm`) from torque and velocity derivatives.  
3. Dynamically scales PICA reward weights based on the proxy’s percentile position.  
4. Validates the approach with a **GLMM** statistical test and a **correlation‑validation** experiment.  

## Quick Start

See `quickstart.md` for detailed installation and execution instructions. The main entry point is:

```bash
python code/main.py --mode full
```

## Reproducibility

- All random seeds are pinned (default seed = 42, overridable via `--seed`).  
- Dependencies are fixed in `requirements.txt`.  
- Generated files are checksummed; hashes are recorded in the project state YAML.  

## Project Layout

```
code/
│   main.py                # Orchestrates the full pipeline
│   environment/
│       drag_mesh_env.py   # PyBullet wrapper (CPU only)
│       articulated_object_gen.py
│   estimators/
│       virtual_tactile.py # Implements FR‑001, FR‑006, FR‑007
│   policies/
│       static_pica.py
│       adaptive_pica.py   # Implements FR‑002, FR‑011
│   analysis/
│       statistical_test.py
data/
│   raw/
│       dragmesh_manifest.jsonl
│   generated/
│       novel_objects/
│   logs/
│       simulation_run_*.csv
│       experiment_summary.json
tests/
│   unit/
│   integration/
│   contract/
contracts/
│   *.schema.yaml
docs/
    README.md
    CHANGELOG.md
requirements.txt
```

## License

This project is released under the MIT License.

---
