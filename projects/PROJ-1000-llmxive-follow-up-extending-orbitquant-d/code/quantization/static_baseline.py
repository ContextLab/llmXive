import torch

def get_static_rotation_matrix(dim: int, seed: int = 42) -> torch.Tensor:
    """
    Generates a deterministic orthogonal rotation matrix using QR decomposition.

    Parameters
    ----------
    dim : int
        Desired dimensionality (the matrix will be ``dim × dim``).
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    torch.Tensor
        Orthogonal rotation matrix of shape ``(dim, dim)``.
    """
    torch.manual_seed(seed)
    # Random normal matrix → QR decomposition → orthogonal Q
    q, _ = torch.linalg.qr(torch.randn(dim, dim))
    return q
