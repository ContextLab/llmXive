"""
src/run_pipeline.py
-------------------
Compatibility wrapper that provides both a callable ``run_pipeline`` function
and a CLI entry point.  The function forwards to the orchestrator defined in
``code.src.pipeline`` so that legacy imports like ``from src import run_pipeline``
work as expected.  The ``main`` function mirrors the original CLI behaviour
and delegates to the implementation in ``code.src.run_pipeline``.
"""

from __future__ import annotations

from typing import Any

# Import the orchestrator function (the core pipeline implementation).
from code.src.pipeline import run_pipeline as _orchestrator

# Import the original CLI ``main`` for command‑line usage.
from code.src.run_pipeline import main as _cli_main


def run_pipeline(
    subjects: int = 5,
    dry_run: bool = False,
    hcp_token: str | None = None,
    fd_threshold: float = 0.2,
    entropy_r: float = 0.15,
    entropy_m: int = 2,
    scales: tuple[int, ...] = (1, 2, 3, 4, 5),
    batch_size: int = 50,
    **kwargs: Any,
) -> None:
    """
    Public wrapper that mirrors ``code.src.pipeline.run_pipeline``.

    Parameters
    ----------
    subjects : int
        Number of subjects to process.
    dry_run : bool
        If True, skips all heavy processing (used by the test suite).
    hcp_token : str | None
        Optional HCP access token; passed through to the download stage.
    fd_threshold : float
        Motion threshold for quality control.
    entropy_r, entropy_m, scales, batch_size :
        Parameters forwarded to the entropy stage.
    kwargs :
        Additional keyword arguments are ignored but accepted for forward
        compatibility with earlier versions of the API.
    """
    # Directly delegate to the orchestrator implementation.
    _orchestrator(
        subjects=subjects,
        dry_run=dry_run,
        hcp_token=hcp_token,
        fd_threshold=fd_threshold,
        entropy_r=entropy_r,
        entropy_m=entropy_m,
        scales=scales,
        batch_size=batch_size,
        **kwargs,
    )


def main() -> None:
    """
    CLI entry point that simply forwards to the original implementation
    in ``code.src.run_pipeline``.  This keeps the command‑line interface
    unchanged (``python -m src.run_pipeline``) while ensuring that the
    underlying logic lives in a single place.
    """
    _cli_main()


if __name__ == "__main__":
    main()