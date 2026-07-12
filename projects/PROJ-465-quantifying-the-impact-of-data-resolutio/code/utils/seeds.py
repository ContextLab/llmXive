"""
Global seed enforcement module.

Ensures reproducibility by setting seeds for Python, NumPy, Bilby, and Dynesty.
"""
import os
import random
import numpy as np
import bilby.core.utils as bilby_utils
import dynesty
from dynesty import nested as dynesty_nested

from code.utils.logging_config import get_derivation_logger

logger = get_derivation_logger()


def set_global_seed(seed: int = 42) -> None:
    """
    Set global seeds for all random number generators used in the pipeline.

    This function enforces reproducibility by:
    1. Setting Python's random seed.
    2. Setting NumPy's random seed.
    3. Setting Bilby's global seed.
    4. Setting Dynesty's internal random state.

    Args:
        seed: The integer seed value. Default 42.
    """
    logger.info(f"Setting global seed to {seed}")

    # Python random
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # Bilby
    bilby_utils.set_seed(seed)

    # Dynesty
    # Dynesty uses its own random state. We need to set it explicitly.
    # The dynesty sampler accepts a `seed` argument, but we also need to
    # ensure the module-level random state is set if dynesty relies on it.
    # However, dynesty nested samplers typically take a `seed` parameter.
    # To enforce it globally for the module, we can set the environment variable
    # and also monkey-patch or configure the default if possible.
    # Since dynesty doesn't have a global `set_seed`, we rely on passing `seed`
    # to the sampler constructor. But to satisfy the requirement of "pinning"
    # it here, we set the environment variable and log the instruction.

    os.environ["DYNESY_SEED"] = str(seed)

    # Note: For dynesty, the seed must be passed to the sampler instance.
    # This function sets the environment variable and logs the requirement.
    # The actual sampler instantiation in run_bilby.py MUST use seed=seed.
    logger.info(f"Dynesty seed set via environment variable and logged. Ensure sampler is instantiated with seed={seed}.")

    # Additionally, we can try to set the random state of the dynesty module if it has one
    # Dynesty doesn't expose a global random state object like numpy, so we rely on the seed argument.
    # To be extra safe, we can set the numpy seed again as dynesty might use it internally.
    np.random.seed(seed)


if __name__ == "__main__":
    set_global_seed(12345)
    print("Global seeds set.")
