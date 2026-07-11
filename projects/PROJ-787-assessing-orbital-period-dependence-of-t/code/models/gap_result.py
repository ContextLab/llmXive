"""
Data model for gap analysis results.

Matches contracts/analysis_output.schema.yaml structure.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class GapResult:
    """
    Represents the result of a Gaussian Mixture Model fit for a specific period bin.
    
    Attributes correspond to the schema defined in contracts/analysis_output.schema.yaml.
    """
    # Bin Identification
    bin_id: int
    period_bin_min: float
    period_bin_max: float
    period_bin_center: float
    weighted_mean_period: float
    n_planets: int
    
    # GMM Results
    component_1_mean: float
    component_1_std: float
    component_1_weight: float
    component_2_mean: float
    component_2_std: float
    component_2_weight: float
    gap_location: float
    gap_uncertainty: float
    
    # Model Selection
    bic: float
    aic: float
    model_status: str = "resolved"  # "resolved" or "unresolved"
    
    # Validation
    kde_validation_passed: Optional[bool] = None
    
    # Metadata
    fit_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    fit_seed: Optional[int] = None
    bootstrap_iterations: int = 0
    flags: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "bin_id": self.bin_id,
            "period_bin_min": self.period_bin_min,
            "period_bin_max": self.period_bin_max,
            "period_bin_center": self.period_bin_center,
            "weighted_mean_period": self.weighted_mean_period,
            "n_planets": self.n_planets,
            "component_1_mean": self.component_1_mean,
            "component_1_std": self.component_1_std,
            "component_1_weight": self.component_1_weight,
            "component_2_mean": self.component_2_mean,
            "component_2_std": self.component_2_std,
            "component_2_weight": self.component_2_weight,
            "gap_location": self.gap_location,
            "gap_uncertainty": self.gap_uncertainty,
            "bic": self.bic,
            "aic": self.aic,
            "model_status": self.model_status,
            "kde_validation_passed": self.kde_validation_passed,
            "fit_timestamp": self.fit_timestamp,
            "fit_seed": self.fit_seed,
            "bootstrap_iterations": self.bootstrap_iterations,
            "flags": self.flags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GapResult":
        """Create a GapResult from a dictionary."""
        # Handle missing optional fields gracefully
        required_fields = [
            "bin_id", "period_bin_min", "period_bin_max", "period_bin_center",
            "n_planets", "component_1_mean", "component_1_std", "component_1_weight",
            "component_2_mean", "component_2_std", "component_2_weight",
            "gap_location", "gap_uncertainty", "bic", "aic"
        ]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Convert numeric fields safely
        try:
            for key in required_fields:
                if key != "bin_id" and key != "n_planets":
                    data[key] = float(data[key])
            data["bin_id"] = int(data["bin_id"])
            data["n_planets"] = int(data["n_planets"])
            
            # Handle optional fields
            if "kde_validation_passed" in data and data["kde_validation_passed"] is not None:
                data["kde_validation_passed"] = bool(data["kde_validation_passed"])
                
            if "fit_seed" in data and data["fit_seed"] is not None:
                data["fit_seed"] = int(data["fit_seed"])
                
            if "bootstrap_iterations" not in data:
                data["bootstrap_iterations"] = 0
                
            if "model_status" not in data:
                data["model_status"] = "resolved"
                
            if "flags" not in data:
                data["flags"] = {}
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error converting numeric fields: {e}")
        
        return cls(**data)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "GapResult":
        """Create a GapResult from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """Perform basic validation on the result."""
        if self.n_planets < 30:
            return False
        if self.gap_location <= 0:
            return False
        if self.component_1_weight <= 0 or self.component_2_weight <= 0:
            return False
        if self.component_1_weight + self.component_2_weight > 1.01:
            return False
        return True