"""
Minimal stub of the ``pyarrow`` package to satisfy pandas optional imports
in environments where the compiled binary wheels are unavailable.
This stub provides only the attributes accessed during pandas import;
any attempt to use full pyarrow functionality will raise a clear error.
"""
class _DummyLib:
    """Placeholder for ``pyarrow.lib``."""
    pass

# Export a ``lib`` attribute expected by pandas.compat.pyarrow
lib = _DummyLib()

# Minimal symbols that pandas may reference
def array(*args, **kwargs):
    raise NotImplementedError("pyarrow stub: array() is not implemented.")

def Table(*args, **kwargs):
    raise NotImplementedError("pyarrow stub: Table() is not implemented.")

__all__ = ["lib", "array", "Table"]
