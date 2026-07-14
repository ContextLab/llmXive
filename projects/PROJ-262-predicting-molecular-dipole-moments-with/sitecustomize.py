"""
Minimal ``sitecustomize`` to avoid the broken custom implementation that
previously raised ``AttributeError: module 'importlib' has no attribute 'util'``.

By providing an empty ``sitecustomize`` module at the repository root we
ensure that Python's import system uses the standard library's ``sitecustomize``
(which does nothing) instead of any inadvertently bundled version.
"""
# No custom behaviour required.
pass
