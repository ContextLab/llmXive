from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class AnomalyScore:
    """
    Anomaly score output with probabilistic uncertainty estimates.

    US1 Acceptance Scenario 3: Model produces anomaly scores with
    probabilistic uncertainty that can be used to assess confidence
    in anomaly detection decisions.
    """
    timestamp: datetime
    score: float
    # Probabilistic uncertainty estimates (US1-AS3)
    uncertainty_variance: float = field(default=0.0)
    uncertainty_std: float = field(default=0.0)
    confidence_interval_95: tuple = field(default_factory=lambda: (0.0, 0.0))
    # Probability that this observation is anomalous (posterior)
    posterior_anomaly_prob: float = field(default=0.0)
    # Number of posterior samples used for uncertainty estimation
    n_samples: int = field(default=0)
    # Additional metadata
    component_assignments: Optional[List[int]] = field(default=None)
    component_weights: Optional[Dict[int, float]] = field(default=None)
    elbo_value: Optional[float] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'score': self.score,
            'uncertainty_variance': self.uncertainty_variance,
            'uncertainty_std': self.uncertainty_std,
            'confidence_interval_95': list(self.confidence_interval_95),
            'posterior_anomaly_prob': self.posterior_anomaly_prob,
            'n_samples': self.n_samples,
            'component_assignments': self.component_assignments,
            'component_weights': self.component_weights,
            'elbo_value': self.elbo_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnomalyScore':
        """Load from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            score=data['score'],
            uncertainty_variance=data.get('uncertainty_variance', 0.0),
            uncertainty_std=data.get('uncertainty_std', 0.0),
            confidence_interval_95=tuple(data.get('confidence_interval_95', (0.0, 0.0))),
            posterior_anomaly_prob=data.get('posterior_anomaly_prob', 0.0),
            n_samples=data.get('n_samples', 0),
            component_assignments=data.get('component_assignments'),
            component_weights=data.get('component_weights'),
            elbo_value=data.get('elbo_value'),
        )

    def is_anomalous(self, threshold: float = 0.0) -> bool:
        """Check if score exceeds threshold."""
        return self.score > threshold

    def get_certainty_level(self) -> str:
        """
        Return certainty level based on uncertainty variance.

        Returns:
            'high' if variance < 0.1, 'medium' if < 0.5, 'low' otherwise
        """
        if self.uncertainty_variance < 0.1:
            return 'high'
        elif self.uncertainty_variance < 0.5:
            return 'medium'
        else:
            return 'low'
