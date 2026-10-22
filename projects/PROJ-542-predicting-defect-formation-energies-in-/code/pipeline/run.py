"""
code/pipeline/run.py
--------------------
Wrapper that re-exports the pipeline orchestration logic from src.pipeline.run.
"""

from src.pipeline.run import run as _run_impl, main as _main_impl

def main() -> None:
    """
    CLI entry point used by `python -m code.pipeline.run`.
    """
    _main_impl()

def run():
    """
    Programmatic entry point that executes the pipeline and returns 
    the paths to the primary artifacts.
    """
    return _run_impl()
