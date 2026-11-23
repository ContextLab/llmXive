import numpy as np
from typing import Optional
from config import RANDOM_SEED

def sample_patience(mean_seconds: float = 2.0, seed: Optional[int] = None) -> float:
    """
    Sample user patience from an exponential decay distribution.
    Default mean is 2.0 seconds.
    """
    if seed is not None:
        np.random.seed(seed)
    else:
        np.random.seed(RANDOM_SEED)
    
    # Exponential distribution: lambda = 1 / mean
    # Scale parameter in numpy is 1/lambda = mean
    patience = np.random.exponential(scale=mean_seconds)
    return float(patience)

if __name__ == "__main__":
    print(f"Sampled patience: {sample_patience()}s")
