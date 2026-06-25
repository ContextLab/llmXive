"""
Very small stub of ``matplotlib.pyplot``.

Functions simply accept any arguments and perform no action, returning
``None``.  This is sufficient for scripts that only need to call
``savefig`` or ``close``.
"""

from __future__ import annotations

from typing import Any

def figure(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.figure``."""
    return None

def plot(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.plot``."""
    return None

def savefig(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.savefig``."""
    return None

def close(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.close``."""
    return None

def title(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.title``."""
    return None

def xlabel(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.xlabel``."""
    return None

def ylabel(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.ylabel``."""
    return None

def legend(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.legend``."""
    return None

def grid(*args: Any, **kwargs: Any) -> None:
    """Placeholder for ``matplotlib.pyplot.grid``."""
    return None

# The real module also defines ``rcParams`` etc.; they are not needed here.