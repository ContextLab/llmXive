#!/usr/bin/env bash
set -e
# Wrapper to invoke the Python download routine.
# The Python module is invoked via ``-m src.download download`` which
# triggers the download step defined in ``code/src/download.py``.
python -m src.download download
