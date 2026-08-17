from __future__ import annotations

from typing import Any, Dict, List, Tuple

def create_scatter_plot(
    x: List[float],
    y: List[float],
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: str,
) -> None: ...

def create_residual_plot(
    residuals: List[float],
    *,
    title: str,
    output_path: str,
) -> None: ...

def create_model_comparison_plot(
    models: Dict[str, Tuple[List[float], List[float]]],
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: str,
) -> None: ...

def create_stratified_scatter_plot(
    x: List[float],
    y: List[float],
    groups: List[str],
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    output_path: str,
) -> None: ...

def main() -> None: ...
