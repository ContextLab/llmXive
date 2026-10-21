"""
Wrapper module that re‑exports the global configuration defined in
``code/src/config.py``. Importing ``src.config`` gives access to ``SEED`` and
proxy‑related constants.
"""

from code.src.config import *  # noqa: F401,F403

if __name__ == "__main__":
    # No script‑level behaviour required.
    pass