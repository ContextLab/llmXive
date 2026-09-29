import os
import random
import numpy as np
import torch

def set_seed(seed: int = 42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_seed_info() -> Dict[str, int]:
    return {
        "python": random.getstate()[1][0],
        "numpy": np.random.get_state()[1][0],
        "torch": torch.initial_seed()
    }
