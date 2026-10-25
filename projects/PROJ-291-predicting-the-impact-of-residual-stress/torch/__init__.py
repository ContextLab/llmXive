"""
Minimal stub for the ``torch`` package.

The project’s environment‑check script only verifies that the package can be
imported; it does not rely on any functionality of PyTorch. Providing this
lightweight placeholder avoids the heavyweight binary installation while
satisfying the import requirement.
"""
# The stub deliberately provides no functionality.
# If downstream code accidentally tries to use torch, it will raise an
# informative error indicating that the real package is not installed.
class _MissingTorchError(RuntimeError):
    pass

def __getattr__(name):
    raise _MissingTorchError(
        "The stub ``torch`` package does not implement any attributes. "
        "Install the real PyTorch library if required."
    )
