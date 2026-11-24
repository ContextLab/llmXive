"""
Wrapper script to execute the unit‑metadata generation step.

The quickstart guide expects the command
    python code/generate_units_metadata.py
to produce the required JSON files.  This wrapper simply imports and
invokes the ``main`` function, ensuring that any import‑time side effects
(such as copying CSVs from ``data/source`` to ``data/raw``) are performed
before the pipeline proceeds.
"""

from generate_units_metadata import main

if __name__ == "__main__":
    main()