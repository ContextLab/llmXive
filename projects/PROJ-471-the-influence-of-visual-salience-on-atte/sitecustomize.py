"""
Site‑customization module that patches the read‑only ``paths.root``
attribute provided by ``llmxive_toolkit`` so that test suites (e.g.
``code/tests/test_bootstrap.py``) can assign a temporary directory
during execution.

The upstream ``ProjectPaths.root`` property is defined without a setter,
which raises ``AttributeError`` when a test attempts ``paths.root = ...``.
This module replaces the property with a mutable version that stores the
value in the underlying private attribute (usually ``_root``).
"""

import os
from pathlib import Path

try:
    # Import the original toolkit paths object
    from llmxive_toolkit import paths as _paths
except Exception as exc:
    # If the toolkit cannot be imported for any reason, fail loudly –
    # the bootstrap script depends on it.
    raise RuntimeError("Failed to import llmxive_toolkit.paths") from exc

# The concrete class used by the toolkit (ProjectPaths) is accessible via
# the ``paths`` instance's ``__class__`` attribute.
_ProjectPaths = _paths.__class__

# Preserve the original getter (read‑only) so we can reuse its logic.
_original_getter = _ProjectPaths.root.fget

def _root_setter(self, value):
    """
    Setter that assigns ``value`` to the underlying private attribute.
    The toolkit stores the root path in ``self._root`` (as of the current
    version). If that attribute does not exist we create it.
    """
    # Convert to ``Path`` for consistency.
    new_root = Path(value) if not isinstance(value, Path) else value
    # Directly set the private attribute, bypassing the read‑only property.
    object.__setattr__(self, "_root", new_root)

# Replace the property with a new one that includes our setter.
_ProjectPaths.root = property(_original_getter, _root_setter)

# Ensure that any code importing ``paths`` after this patch sees the
# mutable version.
# (The ``paths`` instance is already created by the toolkit; updating its
# class updates the instance's behavior automatically.)