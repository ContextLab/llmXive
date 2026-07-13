"""Stub implementation of nilearn.input_data to allow project import without the full library."""

class NiftiLabelsMasker:
    """
    Very small stand‑in for the real ``nilearn.input_data.NiftiLabelsMasker``.
    It accepts any arguments but raises ``NotImplementedError`` when used.
    The PCA step does not depend on this class, so the stub is sufficient
    for import‑time compatibility.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def fit(self, *args, **kwargs):
        raise NotImplementedError("NiftiLabelsMasker.fit is not implemented in the stub.")

    def transform(self, *args, **kwargs):
        raise NotImplementedError("NiftiLabelsMasker.transform is not implemented in the stub.")

    def fit_transform(self, *args, **kwargs):
        raise NotImplementedError("NiftiLabelsMasker.fit_transform is not implemented in the stub.")