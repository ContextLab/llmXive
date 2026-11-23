# Neural Mechanisms Underlying Adaptive Decision‑Making

## Reproducibility

All scripts in this repository are designed to be **deterministic** when the
global random seeds are fixed. The seed configuration is centralized in
`code/utils/reproducibility.py`.

### Seed Value

- **SEED = 42** – This constant is defined in `code/utils/reproducibility.py`.
- The module automatically sets the seed for:
 - Python's built‑in `random` module
 - NumPy (`numpy.random`)
 - PyTorch (CPU & CUDA) – if PyTorch is installed

### How to Verify

Run the following command from the project root:

```bash
python -c "import code.utils.reproducibility as r; assert r.SEED == 42"
```

The command should exit with status `0` (no output). If it fails, the
reproducibility module is not correctly installed or the seed constant has
been altered.

### Usage in Scripts

Any script that needs deterministic behavior should import the module
(the import itself applies the seed):

```python
import code.utils.reproducibility as reproducibility
# No further action required; the seed is already set.
```

If you need to reset the seed to a different value for an experimental run,
you can call `reproducibility.seed_all(new_seed)` after the import.

## Project Overview

(The rest of the original README content would follow here.)