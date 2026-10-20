"""
Minimal stub of the `pyspedas.cdaweb` module.

The real `pyspedas` library provides a `cdaweb` function that returns a list
of downloaded file paths. In the test environment the library is not
installed, but the code under test performs a lazy import and expects the
function to exist. This stub satisfies the import and allows the test suite
to patch `pyspedas.cdaweb.cdaweb` as needed.

If called without being patched, the function raises a clear
NotImplementedError so that any accidental use fails loudly, respecting
the project's policy of no silent synthetic fallbacks.
"""
from typing import List

def cdaweb(*args, **kwargs) -> List[str]:
    """
    Stub implementation of `pyspedas.cdaweb.cdaweb`.

    Parameters
    ----------
    *args, **kwargs : Any
        Ignored; present only to match the signature of the real function.

    Returns
    -------
    List[str]
        In a real environment this would be a list of file paths to the
        downloaded CDF files. The stub raises an error to indicate that
        real data download is unavailable.

    Raises
    ------
    NotImplementedError
        Always raised to signal that real data fetching is not supported
        in the test environment.
    """
    raise NotImplementedError(
        "pyspedas stub: real data download not implemented in this test environment."
    )