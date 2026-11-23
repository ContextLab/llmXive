"""Stub module for ``rdt.transformers`` providing the missing ``IDGenerator``.

The real ``rdt.transformers`` module defines many transformer classes.
The ``sdv`` package only requires the presence of ``IDGenerator`` at
import time; the class itself is not used elsewhere in this project.
Implementing a minimal placeholder satisfies the import without
affecting downstream functionality.
"""
class IDGenerator:
    """Placeholder for the missing ``IDGenerator`` class.

    It mimics the interface of the original class sufficiently for
    import-time checks. All methods raise ``NotImplementedError`` to
    make any accidental use obvious.
    """
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "IDGenerator is a stub; real functionality is unavailable."
        )
