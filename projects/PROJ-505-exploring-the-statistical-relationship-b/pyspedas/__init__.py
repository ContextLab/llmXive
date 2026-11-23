"""
Stub package for pyspedas to allow imports in environments where the real
pyspedas library is not installed. The real implementation is not required
for the unit tests; they either patch the `cdaweb.cdaweb` function or
expect it to raise an ImportError when used.
"""
# No symbols are exported; the submodule `cdaweb` provides the required API.
