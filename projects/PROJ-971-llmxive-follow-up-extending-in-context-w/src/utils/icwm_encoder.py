"""
icwm_encoder.py
----------------

Minimal CPU‑only encoder for the ICWM pipeline.

The real project would ship a sophisticated pretrained encoder. For the
purposes of this repository we provide a deterministic, lightweight
implementation that operates on the raw ``states``, ``actions`` and
``observations`` arrays produced by ``generate_clips``.

The encoder concatenates the three modalities per timestep, centers the
data and applies a truncated singular‑value decomposition (SVD). The
resulting low‑dimensional token matrix is returned as a ``np.ndarray`` of
shape ``(T, D)`` where ``T`` is the number of timesteps and ``D`` is the
chosen latent dimensionality (default 5). This deterministic transformation
is sufficient for computing the statistical descriptors required by
``extract_descriptors.py``.
"""

from __future__ import annotations

import numpy as np

__all__ = ["encode"]


def encode(
    states: np.ndarray,
    actions: np.ndarray,
    observations: np.ndarray,
    latent_dim: int = 5,
) -> np.ndarray:
    """
    Encode raw interaction data into a latent token sequence.

    Parameters
    ----------
    states : np.ndarray
        Array of shape ``(T, S)`` where ``S`` is the state dimension.
    actions : np.ndarray
        Array of shape ``(T, A)`` where ``A`` is the action dimension.
    observations : np.ndarray
        Array of shape ``(T, O)`` where ``O`` is the observation dimension.
    latent_dim : int, optional
        Desired dimensionality of the latent token space (default 5).

    Returns
    -------
    np.ndarray
        Token matrix of shape ``(T, latent_dim)``.
    """
    # Verify consistent timestep dimension.
    if not (states.shape[0] == actions.shape[0] == observations.shape[0]):
        raise ValueError(
            "All input arrays must have the same number of timesteps (first dimension)."
        )

    # Concatenate modalities along the feature axis.
    # Resulting shape: (T, S + A + O)
    concatenated = np.concatenate([states, actions, observations], axis=1)

    # Center the data (zero‑mean) – deterministic, no random seed needed.
    mean = concatenated.mean(axis=0, keepdims=True)
    centered = concatenated - mean

    # Compute SVD. For efficiency on small arrays we use full SVD.
    # ``U`` has shape (T, T), ``s`` (min(T, F)), ``Vt`` (F, F) where F is feature dim.
    # We keep the first ``latent_dim`` right‑singular vectors.
    # If ``latent_dim`` exceeds the feature dimension we cap it.
    max_dim = min(latent_dim, centered.shape[1])
    # Using ``np.linalg.svd`` with ``full_matrices=False`` gives U shape (T, F).
    U, s, Vt = np.linalg.svd(centered, full_matrices=False)
    tokens = U[:, :max_dim] * s[:max_dim]  # scale by singular values
    return tokens.astype(np.float32)