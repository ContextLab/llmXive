from __future__ import annotations

from dataclasses import dataclass
from typing import List

@dataclass
class ResidualFamily:
    name: str
    indices: List[int]
    mean_residual: float
    std_residual: float

def identify_residual_families(
    residuals: List[float],
    *,
    threshold: float = 2.0,
) -> List[ResidualFamily]: ...

def write_residual_analysis_report(
    families: List[ResidualFamily],
    output_path: str,
) -> None: ...

def main() -> None: ...
