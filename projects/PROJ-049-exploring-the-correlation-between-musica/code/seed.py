import random
import numpy as np
import hashlib
from pathlib import Path

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Optional torch seed (if torch is installed)
try:
    import torch
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
except ImportError:
    pass

# Write SHA-256 hash of this file to seed_hash.txt
# This ensures that the hash is updated whenever the seed configuration changes.
_this_path = Path(__file__)
_hash_path = _this_path.parent / "seed_hash.txt"
try:
    _content = _this_path.read_bytes()
    _sha256 = hashlib.sha256(_content).hexdigest()
    _hash_path.write_text(_sha256)
except Exception:
    # Fail silently on hash write to avoid blocking imports in restricted environments
    pass
