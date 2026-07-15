"""
Base data models for the Prime Gap and Riemann Zeta Zero analysis pipeline.

This module defines the core entities (PrimeGap, ZetaZero, WindowStats)
used throughout the data ingestion, analysis, and robustness phases.
These models ensure type safety and structural consistency across the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import math

class GapStatus(Enum):
    """Status of a prime gap relative to expected Cramér prediction."""
    NORMAL = "normal"
    EXCESSIVE = "excessive"
    DEFICIENT = "deficient"

@dataclass(frozen=True)
class PrimeGap:
    """
    Represents a single gap between consecutive prime numbers.

    Attributes:
        prime_before: The smaller prime number (p_n).
        prime_after: The larger prime number (p_{n+1}).
        gap_size: The raw difference (p_{n+1} - p_n).
        normalized_gap: The gap size normalized by log^2(p), per Cramér model.
        status: Classification of the gap relative to the mean expectation.
    """
    prime_before: int
    prime_after: int
    gap_size: int
    normalized_gap: float
    status: GapStatus = GapStatus.NORMAL

    def __post_init__(self):
        # Validate consistency
        if self.prime_after <= self.prime_before:
            raise ValueError("prime_after must be strictly greater than prime_before")
        if self.gap_size != (self.prime_after - self.prime_before):
            raise ValueError("gap_size must equal prime_after - prime_before")
        
        # Recalculate normalized gap to ensure consistency if passed incorrectly
        # Using natural log as per standard analytic number theory convention
        if self.prime_before < 2:
            raise ValueError("prime_before must be >= 2")
        
        log_p = math.log(self.prime_before)
        expected_gap = log_p * log_p
        if expected_gap == 0:
            raise ValueError("log^2(p) cannot be zero")
        
        # Ensure the stored normalized_gap matches calculation within float precision
        # or recalculate if the provided one is nonsensical (though dataclass init doesn't run this logic automatically)
        # We trust the caller to provide correct values, but we can enforce the status logic here.
        
        # Re-calculate status based on normalized gap
        # A gap is "excessive" if it exceeds the expected log^2 p significantly (e.g. > 1.5x)
        # A gap is "deficient" if it is significantly smaller (e.g. < 0.5x)
        # These thresholds are heuristic and can be adjusted based on spec.
        if self.normalized_gap > 1.5:
            object.__setattr__(self, 'status', GapStatus.EXCESSIVE)
        elif self.normalized_gap < 0.5:
            object.__setattr__(self, 'status', GapStatus.DEFICIENT)
        else:
            object.__setattr__(self, 'status', GapStatus.NORMAL)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (e.g., CSV, JSON)."""
        return {
            "prime_before": self.prime_before,
            "prime_after": self.prime_after,
            "gap_size": self.gap_size,
            "normalized_gap": self.normalized_gap,
            "status": self.status.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrimeGap":
        """Construct from dictionary."""
        return cls(
            prime_before=int(data["prime_before"]),
            prime_after=int(data["prime_after"]),
            gap_size=int(data["gap_size"]),
            normalized_gap=float(data["normalized_gap"]),
            status=GapStatus(data.get("status", "normal"))
        )


@dataclass(frozen=True)
class ZetaZero:
    """
    Represents a non-trivial zero of the Riemann Zeta function.
    
    According to the Riemann Hypothesis, all non-trivial zeros lie on the
    critical line Re(s) = 1/2. This model stores the imaginary part (gamma)
    of the zero s = 1/2 + i*gamma.

    Attributes:
        index: The ordinal index of the zero (n-th zero).
        gamma: The imaginary part of the zero (t value).
        source: The source of the data (e.g., "LMFDB", "Odlyzko").
        verified: Whether the zero has been verified against a trusted source.
    """
    index: int
    gamma: float
    source: str = "unknown"
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "index": self.index,
            "gamma": self.gamma,
            "source": self.source,
            "verified": self.verified
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZetaZero":
        """Construct from dictionary."""
        return cls(
            index=int(data["index"]),
            gamma=float(data["gamma"]),
            source=data.get("source", "unknown"),
            verified=bool(data.get("verified", False))
        )


@dataclass
class WindowStats:
    """
    Aggregated statistics for a sliding window of prime gaps.
    
    Used in the analysis phase (US2) to compute distributions of maximal gaps
    within specific ranges of the number line.

    Attributes:
        window_start: The starting prime or value of the window.
        window_end: The ending prime or value of the window.
        count: Number of gaps in this window.
        max_gap: The largest gap found in this window.
        max_gap_normalized: The normalized value of the max gap.
        mean_gap: Average gap size in the window.
        std_gap: Standard deviation of gap sizes in the window.
        gaps: List of all gap objects in the window (optional, for memory efficiency
              this might be omitted in production, but kept for analysis flexibility).
    """
    window_start: int
    window_end: int
    count: int
    max_gap: float
    max_gap_normalized: float
    mean_gap: float
    std_gap: float
    gaps: Optional[List[PrimeGap]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "window_start": self.window_start,
            "window_end": self.window_end,
            "count": self.count,
            "max_gap": self.max_gap,
            "max_gap_normalized": self.max_gap_normalized,
            "mean_gap": self.mean_gap,
            "std_gap": self.std_gap,
            # Do not serialize the full list of gaps to keep JSON/CSV small unless needed
            "gaps_count": len(self.gaps) if self.gaps else 0
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowStats":
        """Construct from dictionary. Note: gaps list is not reconstructed from dict."""
        return cls(
            window_start=int(data["window_start"]),
            window_end=int(data["window_end"]),
            count=int(data["count"]),
            max_gap=float(data["max_gap"]),
            max_gap_normalized=float(data["max_gap_normalized"]),
            mean_gap=float(data["mean_gap"]),
            std_gap=float(data["std_gap"]),
            gaps=[]
        )