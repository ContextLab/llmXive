"""
Minimal logging helper used by ``experiments.runner``.

The original project expected a ``utils.logging_setup`` module providing a
``get_experiment_logger`` function that returns a configured ``logging.Logger``.
For the purposes of the profiling task we can forward to the central
``llmxive_toolkit.get_logger`` implementation.
"""
from llmxive_toolkit import get_logger

def get_experiment_logger(name: str):
    """
    Return a logger instance for experiment components.

    Parameters
    ----------
    name: str
        Name of the logger (usually the module name).

    Returns
    -------
    logging.Logger
    """
    return get_logger(name)
