"""
Mask utilities for the geometry extension project.

This module provides two public functions:

* ``load_mask(seed) -> torch.Tensor`` – Load a previously saved mask for a
  given ``seed``. Masks are stored as ``.pt`` files under ``data/masks`` with
  the naming convention ``mask_opd_{seed}.pt``. The function returns the
  deserialized object, which is typically a ``dict`` mapping parameter names
  to binary ``torch.Tensor`` masks, but for backward compatibility a plain
  ``torch.Tensor`` is also accepted.

* ``apply_mask(model, mask)`` – Apply a binary mask to a ``torch.nn.Module``.
  If ``mask`` is a dictionary, each entry is matched to a parameter by name.
  If it is a single tensor, the tensor is broadcast‑multiplied with each
  parameter whose shape matches; otherwise a ``ValueError`` is raised.
  The operation is performed **in‑place** on the model's parameters.

The implementation deliberately avoids any side‑effects other than loading
the mask file and mutating the model. It raises clear errors when the mask
file is missing or when shapes are incompatible.
"""

from __future__ import annotations

import pathlib
from typing import Dict, Mapping, Union

import torch
from torch import nn

__all__ = ["load_mask", "apply_mask"]


def _mask_directory() -> pathlib.Path:
    """
    Resolve the directory where mask files are stored.

    The project stores masks under ``<project_root>/data/masks``.  This
    helper computes that path relative to the location of this file and
    creates the directory if it does not exist.
    """
    # ``mask.py`` lives in ``code/src/model``; the project root is two
    # levels up (``code``).  The data directory is therefore at
    # ``code/data/masks``.
    project_root = pathlib.Path(__file__).resolve().parents[2]
    mask_dir = project_root / "data" / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)
    return mask_dir


def load_mask(seed: int) -> Union[torch.Tensor, Dict[str, torch.Tensor]]:
    """
    Load a mask for the given ``seed`` from disk.

    Parameters
    ----------
    seed: int
        The seed identifier used when the mask was generated.

    Returns
    -------
    Union[torch.Tensor, Dict[str, torch.Tensor]]
        The deserialized mask object.  Historically masks have been saved
        either as a single ``torch.Tensor`` or as a ``dict`` mapping
        parameter names to per‑parameter binary tensors.

    Raises
    ------
    FileNotFoundError
        If the mask file does not exist.
    RuntimeError
        If the file cannot be deserialized by ``torch.load``.
    """
    mask_dir = _mask_directory()
    mask_path = mask_dir / f"mask_opd_{seed}.pt"

    if not mask_path.is_file():
        raise FileNotFoundError(f"Mask file not found for seed {seed}: {mask_path}")

    # ``torch.load`` will raise its own errors if the file is corrupted.
    mask = torch.load(mask_path, map_location="cpu")
    if not isinstance(mask, (torch.Tensor, dict)):
        raise RuntimeError(
            f"Loaded mask has unsupported type {type(mask)}; expected "
            "torch.Tensor or dict[str, torch.Tensor]"
        )
    return mask


def apply_mask(
    model: nn.Module,
    mask: Union[torch.Tensor, Mapping[str, torch.Tensor]],
) -> None:
    """
    Apply a binary mask to the parameters of ``model`` in‑place.

    The mask can be supplied either as a dictionary mapping parameter
    names (as returned by ``model.named_parameters()``) to binary tensors,
    or as a single tensor that is broadcast‑compatible with each parameter
    tensor.

    Parameters
    ----------
    model: torch.nn.Module
        The model whose parameters will be masked.
    mask: Union[torch.Tensor, Mapping[str, torch.Tensor]]
        Binary mask(s).  Values must be 0 or 1; any non‑binary values will
        raise a ``ValueError``.

    Raises
    ------
    ValueError
        If the mask shape does not match a parameter shape or if the mask
        contains values other than 0 or 1.
    """
    if isinstance(mask, Mapping):
        # Dictionary‑based masking
        for name, param in model.named_parameters():
            if name not in mask:
                raise ValueError(f"Mask missing entry for parameter '{name}'")
            param_mask = mask[name]
            if not isinstance(param_mask, torch.Tensor):
                raise ValueError(
                    f"Mask entry for '{name}' is not a torch.Tensor"
                )
            if param_mask.shape != param.shape:
                raise ValueError(
                    f"Mask shape {param_mask.shape} does not match shape of "
                    f"parameter '{name}' ({param.shape})"
                )
            if not ((param_mask == 0) | (param_mask == 1)).all():
                raise ValueError(
                    f"Mask for parameter '{name}' contains non‑binary values"
                )
            # In‑place multiplication
            param.data.mul_(param_mask)
    else:
        # Single‑tensor masking
        if not isinstance(mask, torch.Tensor):
            raise ValueError(
                "Mask must be a torch.Tensor or a mapping of parameter names "
                "to torch.Tensors"
            )
        if not ((mask == 0) | (mask == 1)).all():
            raise ValueError("Mask tensor contains non‑binary values")
        for name, param in model.named_parameters():
            if mask.shape != param.shape:
                raise ValueError(
                    f"Mask shape {mask.shape} does not match shape of "
                    f"parameter '{name}' ({param.shape})"
                )
            param.data.mul_(mask)