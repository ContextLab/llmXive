"""
Wrapper script to invoke the dataset download pipeline.

This script exists solely to provide an executable entry point that the
CI can call (``python code/data/run_download.py``).  It imports the
``main`` function from ``code.data.download`` and runs it.
"""

from code.data.download import main

if __name__ == "__main__":
    main()