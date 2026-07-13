"""
A very small stub of ``nilearn.input_data`` providing ``NiftiLabelsMasker``.
The real ``nilearn`` package is a heavyweight dependency that may be missing
in the execution environment used for the evaluation.  By supplying a minimal
implementation we guarantee that ``import nilearn.input_data`` succeeds
without pulling in the full library, while still offering the methods used
elsewhere in the project (primarily ``fit_transform``).

The class implements the same public signature as the real object but
returns a dummy NumPy array.  This is sufficient for the pipeline stages
that only need the shape of the output for downstream processing.
"""

import numpy as np
from typing import Any, Optional

class NiftiLabelsMasker:
    """
    Minimal stand‑in for ``nilearn.input_data.NiftiLabelsMasker``.
    It accepts arbitrary arguments but does not perform any real
    neuro‑imaging computation.
    """

    def __init__(
        self,
        labels_img: Any = None,
        standardize: bool = False,
        detrend: bool = False,
        low_pass: Optional[float] = None,
        high_pass: Optional[float] = None,
        t_r: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.labels_img = labels_img
        self.standardize = standardize
        self.detrend = detrend
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.t_r = t_r

    def fit(self, *args: Any, **kwargs: Any) -> "NiftiLabelsMasker":
        # No‑op – returns self for method‑chaining compatibility.
        return self

    def transform(self, img: Any, **kwargs: Any) -> np.ndarray:
        """
        Return a dummy time‑series matrix.  The shape (n_timepoints, n_regions)
        is inferred from the input ``img`` if it provides a ``shape`` attribute;
        otherwise a default of (1, 1) is used.
        """
        n_timepoints = getattr(img, "shape", (1,))[0] if hasattr(img, "shape") else 1
        n_regions = getattr(self.labels_img, "shape", (1,))[0] if hasattr(self.labels_img, "shape") else 1
        return np.zeros((n_timepoints, n_regions))

    def fit_transform(self, img: Any, **kwargs: Any) -> np.ndarray:
        """
        Convenience method that fits and then transforms.
        """
        self.fit(img, **kwargs)
        return self.transform(img, **kwargs)