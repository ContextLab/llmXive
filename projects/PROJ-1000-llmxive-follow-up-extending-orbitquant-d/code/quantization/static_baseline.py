import torch

def get_static_rotation_matrix(dim: int, seed: int = 42) -> torch.Tensor:
    """
    Generates a static orthogonal rotation matrix using QR decomposition.
    """
    torch.manual_seed(seed)
    # Create a random matrix and use QR to get an orthogonal Q
    q, r = torch.linalg.qr(torch.randn(dim, dim))
    return q
