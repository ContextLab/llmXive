from __future__ import annotations

from typing import Any, List, Tuple

# Composite metric functions
def combined_complexity_score(*args: Any, **kwargs: Any) -> float: ...

def weighted_entropy_metric(*args: Any, **kwargs: Any) -> float: ...

def compute_metric_from_diagram(*args: Any, **kwargs: Any) -> float: ...

def composite_complexity(*args: Any, **kwargs: Any) -> float: ...

def evaluate_correlation(*args: Any, **kwargs: Any) -> float: ...

def compute_linear_composite(*args: Any, **kwargs: Any) -> float: ...

def evaluate_composite_metric(*args: Any, **kwargs: Any) -> float: ...

def novel_composite_metric(*args: Any, **kwargs: Any) -> float: ...

# Exported names matching the public API
__all__: List[str] = [
    "combined_complexity_score",
    "weighted_entropy_metric",
    "compute_metric_from_diagram",
    "composite_complexity",
    "evaluate_correlation",
    "compute_linear_composite",
    "evaluate_composite_metric",
    "novel_composite_metric",
]