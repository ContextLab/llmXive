"""
code/src/data/download_gwtc.py

Thin wrapper that invokes the production download implementation
located in ``src.data.download``.  The wrapper exists because the
original task specification referred to a script named
``download_gwtc.py`` under ``code/src/data``.  Keeping the logic in a
single module (``src.data.download``) avoids duplication while satisfying
the expected import path.
"""

from src.data.download import main

if __name__ == "__main__":
    # Running this module performs the full GWTC download workflow.
    main()
