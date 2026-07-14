"""
Basic sanity test for the NumPy shim introduced in ``code/numpy/__init__.py``.
The test simply verifies that ``import numpy as np`` provides the expected
``__version__`` attribute and that basic array operations work.
"""

import unittest

class TestNumPyShim(unittest.TestCase):
    def test_import_and_version(self):
        import numpy as np
        self.assertTrue(hasattr(np, "__version__"))
        # Simple operation to ensure the real implementation is used.
        arr = np.arange(5)
        self.assertEqual(arr.tolist(), [0, 1, 2, 3, 4])

if __name__ == "__main__":
    unittest.main()
