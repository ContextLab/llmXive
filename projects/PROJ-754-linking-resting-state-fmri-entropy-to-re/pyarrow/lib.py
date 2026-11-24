"""
Minimal stub for ``pyarrow.lib`` required by pandas' compatibility layer.

Only the ``_ARRAY_API`` attribute is accessed during pandas import.
The rest of the API is intentionally omitted because the project
never calls ``pyarrow`` functions.
"""
_ARRAY_API = True

# Stub objects that pandas may reference if it attempts deeper use.
class Array:
    pass

class Table:
    pass

def array(*args, **kwargs):
    raise NotImplementedError("pyarrow stub – array functionality is not available.")

# Export names that pandas expects to exist.
__all__ = ["_ARRAY_API", "Array", "Table", "array"]