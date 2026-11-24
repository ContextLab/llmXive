"""
This file is intentionally excluded from pytest collection.
The actual unit tests live in ``tests/unit/test_setup_project_structure.py``.
Setting ``__test__ = False`` prevents pytest from importing this module,
which avoids a name‑collision with the unit‑test module of the same name.
"""
__test__ = False
# No executable code – the real tests are in the unit subpackage.