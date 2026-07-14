"""
sitecustomize.py

This module is automatically imported by Python's ``site`` machinery (if it
is importable on ``sys.path``).  Its sole purpose is to patch the NumPy
namespace so that legacy libraries such as pandas, which still reference
deprecated aliases like ``np.int`` or ``np.float_``, can be imported without
raising ``AttributeError`` on NumPy 2.x.

The patch adds the most common aliases that pandas expects.  It does **not**
modify NumPy's behaviour – the aliases simply point to the appropriate
concrete dtypes.
"""

import numpy as np

# Integer aliases
np.int_ = np.int64
np.intc = np.int64
np.intp = np.int64
np.int8 = np.int8 if hasattr(np, "int8") else np.int64
np.int16 = np.int16 if hasattr(np, "int16") else np.int64
np.int32 = np.int32 if hasattr(np, "int32") else np.int64
np.int64 = np.int64

# Unsigned integer aliases
np.uint = np.uint64
np.uint8 = np.uint8 if hasattr(np, "uint8") else np.uint64
np.uint16 = np.uint16 if hasattr(np, "uint16") else np.uint64
np.uint32 = np.uint32 if hasattr(np, "uint32") else np.uint64
np.uint64 = np.uint64

# Float aliases
np.float_ = np.float64
np.float16 = np.float16 if hasattr(np, "float16") else np.float64
np.float32 = np.float32 if hasattr(np, "float32") else np.float64
np.float64 = np.float64

# Bool alias
np.bool_ = np.bool_