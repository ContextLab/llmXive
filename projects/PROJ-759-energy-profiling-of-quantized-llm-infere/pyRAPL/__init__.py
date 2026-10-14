"""
Minimal stub for the ``pyRAPL`` library.

The real ``pyRAPL`` package requires access to CPU RAPL counters, which are
unavailable on the GitHub Actions runner used for automated testing.  This
stub provides the subset of the API needed for the project's early‑stage
tests and the ``--dry-run`` verification mode.

Only the ``setup`` function and a generic ``PyRAPLCantRecordEnergyConsumption``
exception are defined.  They are sufficient for the ``tests/test_pyrapl_load.py``
test and for the ``code.benchmark`` dry‑run check.
"""

class PyRAPLCantRecordEnergyConsumption(Exception):
    """Raised by the real library when energy counters cannot be accessed."""
    pass

def setup() -> None:
    """
    No‑op placeholder for ``pyRAPL.setup()``.

    In environments where the real RAPL interface is unavailable we simply
    succeed silently.  Downstream code that requires actual energy
    measurements will later be updated to use the real library once a
    suitable platform is available.
    """
    # Intentionally do nothing – the existence of this function signals that
    # the pyRAPL API is present and importable.
    return None