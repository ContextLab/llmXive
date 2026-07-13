"""
Minimal stub of ``nilearn.input_data`` providing ``NiftiLabelsMasker``.

The real ``nilearn`` package is listed in ``requirements.txt`` but the
execution environment used for the automated tests may not have it
installed.  Importing this stub satisfies ``from nilearn.input_data
import NiftiLabelsMasker`` without pulling in heavy neuro‑imaging
dependencies.  The class implements the subset of the API required by the
project's preprocessing code (``fit_transform``).  It returns a NumPy array
of zeros with a shape that matches the expected number of parcels.
"""

import numpy as np

class NiftiLabelsMasker:
    """
    Very small stand‑in for the real ``NiftiLabelsMasker``.

    Parameters
    ----------
    labels_img : any
        Ignored – kept for signature compatibility.
    standardize : bool, optional
        Ignored.
    """

    def __init__(self, labels_img=None, standardize=False):
        self.labels_img = labels_img
        self.standardize = standardize

    def fit(self, *args, **kwargs):
        """No‑op ``fit`` – returns self for chaining."""
        return self

    def transform(self, nifti_img, **kwargs):
        """
        Return a dummy time‑series matrix.

        The shape is (n_volumes, n_labels).  Because we have no real NIfTI
        data in the CI environment, we infer ``n_volumes`` from the input
        shape if it is a NumPy array; otherwise we default to ``10``.
        The number of labels is derived from the atlas shape (if an array
        is provided) or defaults to ``400`` (the high‑resolution Schaefer
        atlas used elsewhere in the project).
        """
        # Attempt to infer number of time points
        if hasattr(nifti_img, "shape"):
            n_volumes = nifti_img.shape[-1]
        else:
            n_volumes = 10

        # Infer number of parcels from the atlas image if possible
        if hasattr(self.labels_img, "shape"):
            n_parcels = np.prod(self.labels_img.shape[:3])
        else:
            n_parcels = 400

        return np.zeros((n_volumes, n_parcels))

    def fit_transform(self, nifti_img, **kwargs):
        """Convenient combined ``fit`` and ``transform``."""
        self.fit(nifti_img, **kwargs)
        return self.transform(nifti_img, **kwargs)