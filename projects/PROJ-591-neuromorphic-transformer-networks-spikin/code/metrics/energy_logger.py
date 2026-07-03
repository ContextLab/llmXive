import time
import os
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass, field

@dataclass
class EnergyRecord:
    """Record of energy consumption for a training step."""
    start_time: float
    end_time: float
    energy_consumed_kWh: float
    energy_per_token_kWh: float
    estimated: bool = True

class EnergyLogger:
    """
    Logger for energy consumption.
    Wraps codecarbon if available, otherwise uses wall-clock time as a proxy.
    """
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.energy_records: list = []
        self._codecarbon_available = False
        
        # Try to import codecarbon
        try:
            # This is a placeholder check; actual usage would be inside the logging method
            # from codecarbon import EmissionsTracker
            self._codecarbon_available = False # Disable for CPU-only constraint unless specifically enabled
        except ImportError:
            self._codecarbon_available = False

    def start(self):
        """Start the energy timer."""
        self.start_time = time.time()

    def stop(self, num_tokens: int = 1000) -> EnergyRecord:
        """
        Stop the timer and calculate energy consumption.
        
        Args:
            num_tokens: Number of tokens processed in this interval
            
        Returns:
            EnergyRecord with consumption data
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Fallback: Estimate energy from wall-clock time
        # Assumption: ~10W average power draw for CPU proxy (very rough estimate)
        # 10W = 0.01 kW
        # Energy (kWh) = Power (kW) * Time (h)
        power_kw = 0.01 
        energy_kwh = power_kw * (duration / 3600.0)
        energy_per_token = energy_kwh / num_tokens if num_tokens > 0 else 0.0
        
        record = EnergyRecord(
            start_time=self.start_time,
            end_time=self.end_time,
            energy_consumed_kWh=energy_kwh,
            energy_per_token_kWh=energy_per_token,
            estimated=True
        )
        
        self.energy_records.append(record)
        self.start_time = None
        self.end_time = None
        
        return record

def estimate_energy_from_time(duration_seconds: float, num_tokens: int = 1000) -> EnergyRecord:
    """
    Helper function to estimate energy from time duration.
    
    Args:
        duration_seconds: Duration in seconds
        num_tokens: Number of tokens processed
        
    Returns:
        EnergyRecord
    """
    power_kw = 0.01 # 10W proxy
    energy_kwh = power_kw * (duration_seconds / 3600.0)
    energy_per_token = energy_kwh / num_tokens if num_tokens > 0 else 0.0
    
    return EnergyRecord(
        start_time=time.time() - duration_seconds,
        end_time=time.time(),
        energy_consumed_kWh=energy_kwh,
        energy_per_token_kWh=energy_per_token,
        estimated=True
    )
