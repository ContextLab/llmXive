"""
Helper script to invoke the dataset download pipeline.
This module simply imports the main entry point from ``code.data.download``
and executes it when run as a script.
"""

from code.data.download import main

if __name__ == "__main__":
    main()