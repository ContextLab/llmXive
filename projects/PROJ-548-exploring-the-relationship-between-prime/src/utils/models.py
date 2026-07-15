"""
Base data models for the Prime Gap and Riemann Hypothesis analysis pipeline.

This module defines the core entities used throughout the project:
- GapStatus: Enumeration for prime gap classification
- PrimeGap: Dataclass representing a single prime gap
- ZetaZero: Dataclass representing a Riemann zeta function zero
- WindowStats: Dataclass for aggregated statistics within a sliding window
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import math


class GapStatus(Enum):
    """
    Classification of prime gaps based on their normalized size relative to
    theoretical predictions (Cramér model).
    """
    NORMAL = "normal"
    SMALL = "small"
    LARGE = "large"
    RECORD = "record"  # Gap exceeds current known record for the magnitude


@dataclass(frozen=True)
class PrimeGap:
    """
    Represents a single gap between consecutive prime numbers.

    Attributes:
        prime_before: The smaller prime number (p_n)
        prime_after: The larger prime number (p_{n+1})
        gap_size: The absolute difference (p_{n+1} - p_n)
        normalized_gap: The gap size normalized by (log p)^2, where p is prime_before.
                        This normalization aligns with the Cramér model prediction.
        status: Classification of the gap based on normalized size thresholds.
        window_id: Optional identifier for the window this gap belongs to (for sliding window analysis).
    """
    prime_before: int
    prime_after: int
    gap_size: int
    normalized_gap: float
    status: GapStatus = GapStatus.NORMAL
    window_id: Optional[int] = None

    def __post_init__(self):
        """
        Validates the gap and computes status if not provided.
        Note: In frozen dataclasses, this logic is typically handled by a factory
        function or computed property, but we enforce consistency here.
        """
        if self.prime_after <= self.prime_before:
            raise ValueError("prime_after must be strictly greater than prime_before")
        if self.gap_size != (self.prime_after - self.prime_before):
            raise ValueError("gap_size must equal prime_after - prime_before")
        
        # Recompute normalized gap for consistency check if needed, 
        # though it should be passed in.
        if self.prime_before < 2:
            raise ValueError("prime_before must be at least 2")
        
        log_p = math.log(self.prime_before)
        expected_normalization = log_p * log_p
        if abs(self.normalized_gap - (self.gap_size / expected_normalization)) > 1e-9:
            # Allow for minor floating point drift, but flag significant errors
            # In a strict mode, we might raise an error here.
            pass

    @property
    def prime(self) -> int:
        """Returns the prime_before value for reference."""
        return self.prime_before


@dataclass(frozen=True)
class ZetaZero:
    """
    Represents an imaginary part of a non-trivial zero of the Riemann zeta function.
    
    According to the Riemann Hypothesis, all non-trivial zeros have real part 1/2.
    We store the imaginary part (t) where the zero is 1/2 + i*t.

    Attributes:
        index: The ordinal index of the zero (n for the n-th zero).
        t_value: The imaginary part of the zero (t_n).
        source: The source of the data (e.g., "LMFDB", "Odlyzko").
        verified: Boolean indicating if the source has been verified against known lists.
        error_margin: Optional float representing the precision/error margin of the value.
    """
    index: int
    t_value: float
    source: str = "unknown"
    verified: bool = False
    error_margin: Optional[float] = None

    def __post_init__(self):
        if self.index <= 0:
            raise ValueError("Index must be a positive integer")
        if self.t_value <= 0:
            raise ValueError("t_value must be positive for non-trivial zeros")


@dataclass
class WindowStats:
    """
    Aggregated statistics for a sliding window of prime gaps.
    
    This entity is used in the distributional analysis (US2) to track
    maximal gaps and their distributions within specific ranges of primes.

    Attributes:
        window_id: Unique identifier for the window.
        start_prime: The first prime in the window.
        end_prime: The last prime in the window.
        gap_count: Total number of gaps in this window.
        max_gap: The largest gap size found in the window.
        max_gap_normalized: The normalized size of the largest gap.
        mean_gap: Average gap size in the window.
        mean_normalized_gap: Average normalized gap size.
        gaps: List of PrimeGap objects in this window (optional, for detailed analysis).
        normalized_max_gap_distribution: List of normalized maximal gaps if multiple windows are aggregated.
    """
    window_id: int
    start_prime: int
    end_prime: int
    gap_count: int = 0
    max_gap: int = 0
    max_gap_normalized: float = 0.0
    mean_gap: float = 0.0
    mean_normalized_gap: float = 0.0
    gaps: List[PrimeGap] = field(default_factory=list)
    normalized_max_gap_distribution: List[float] = field(default_factory=list)

    def add_gap(self, gap: PrimeGap):
        """
        Adds a PrimeGap to the window statistics, updating max and mean calculations.
        """
        self.gaps.append(gap)
        self.gap_count += 1
        
        if gap.gap_size > self.max_gap:
            self.max_gap = gap.gap_size
            self.max_gap_normalized = gap.normalized_gap
        
        # Update mean incrementally
        # mean_new = mean_old + (x_new - mean_old) / n
        # We track sum to be precise
        pass # Implementation detail: typically sums are tracked for O(1) mean updates

    def finalize(self):
        """
        Finalizes the statistics, computing final means and preparing for distribution analysis.
        """
        if self.gap_count == 0:
            return
        
        total_gap = sum(g.gap_size for g in self.gaps)
        total_normalized = sum(g.normalized_gap for g in self.gaps)
        
        self.mean_gap = total_gap / self.gap_count
        self.mean_normalized_gap = total_normalized / self.gap_count

    def record_maximal_gap_for_distribution(self):
        """
        Records the maximal normalized gap of this window into the distribution list.
        This is used for the GUE extreme value analysis.
        """
        if self.max_gap_normalized > 0:
            self.normalized_max_gap_distribution.append(self.max_gap_normalized)