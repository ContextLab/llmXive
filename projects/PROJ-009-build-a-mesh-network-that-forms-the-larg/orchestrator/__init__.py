"""
Top‑level ``orchestrator`` package that re‑exports the implementation
located under ``code/orchestrator``.  By adjusting ``__path__`` we make
imports such as ``import orchestrator.logger`` resolve to the actual
module in ``code/orchestrator`` without having to duplicate files.
"""
import pathlib

# Resolve the path of the real implementation folder.
_impl_path = pathlib.Path(__file__).parent.parent / "code" / "orchestrator"

# If the implementation directory exists, add it to this package's
# search path so sub‑modules are found there.
if _impl_path.is_dir():
    __path__ = [_impl_path.as_posix()]
else:
    __path__ = []
