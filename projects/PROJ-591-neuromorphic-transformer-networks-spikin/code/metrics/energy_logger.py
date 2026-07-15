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
        self._codecarbon_tracker = None
        self._codecarbon_available = False
        self._tracking_start_time: Optional[float] = None
        
        # Try to import codecarbon
        try:
            from codecarbon import EmissionsTracker
            # We only enable it if explicitly requested or if we detect a GPU
            # For CPU-only constraint, we default to False but allow override
            self._codecarbon_available = True 
        except ImportError:
            self._codecarbon_available = False

    def enable_codecarbon(self, project_name: str = "neuromorphic-transformer"):
        """
        Enable codecarbon tracking.
        
        Args:
            project_name: Name of the project for codecarbon logging
        """
        if not self._codecarbon_available:
            return False
        
        try:
            from codecarbon import EmissionsTracker
            # Create a tracker that logs to a file or memory
            # We use 'logging' mode to capture emissions without requiring cloud upload
            self._codecarbon_tracker = EmissionsTracker(
                project_name=project_name,
                output_dir="data/logs/codecarbon"
            )
            self._tracking_start_time = time.time()
            self._codecarbon_tracker.start()
            return True
        except Exception as e:
            # Fallback to wall-clock if codecarbon fails to start
            self._codecarbon_tracker = None
            return False

    def start(self):
        """Start the energy timer."""
        self.start_time = time.time()
        if self._codecarbon_tracker:
            # If codecarbon is running, we don't need to start/stop per step
            # The tracker runs for the whole experiment
            pass

    def stop(self, num_tokens: int = 1000) -> EnergyRecord:
        """
        Stop the timer and calculate energy consumption.
        
        Args:
            num_tokens: Number of tokens processed in this interval
            
        Returns:
            EnergyRecord with consumption data
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time if self.start_time else 0.0
        
        energy_kwh = 0.0
        estimated = True

        if self._codecarbon_tracker and hasattr(self._codecarbon_tracker, '_emissions'):
            # Try to get emissions from the tracker if possible
            # Note: codecarbon typically reports total emissions, not per-step
            # We approximate per-step by measuring the duration ratio
            try:
                # This is a simplified approximation; real codecarbon usage
                # would track total experiment energy and divide by total tokens
                # For per-step logging, we use the wall-clock proxy as a fallback
                # but mark it as estimated since codecarbon doesn't support per-step
                # without complex instrumentation
                pass
            except Exception:
                pass

        # Fallback: Estimate energy from wall-clock time
        # Assumption: ~10W average power draw for CPU proxy (very rough estimate)
        # 10W = 0.01 kW
        # Energy (kWh) = Power (kW) * Time (h)
        power_kw = 0.01 
        energy_kwh = power_kw * (duration / 3600.0)
        energy_per_token = energy_kwh / num_tokens if num_tokens > 0 else 0.0
        
        record = EnergyRecord(
            start_time=self.start_time if self.start_time else 0.0,
            end_time=self.end_time if self.end_time else 0.0,
            energy_consumed_kWh=energy_kwh,
            energy_per_token_kWh=energy_per_token,
            estimated=estimated
        )
        
        self.energy_records.append(record)
        self.start_time = None
        self.end_time = None
        
        return record

    def finalize(self):
        """
        Finalize the logger and stop codecarbon tracking if active.
        This should be called at the end of the experiment.
        """
        if self._codecarbon_tracker:
            try:
                self._codecarbon_tracker.stop()
                self._codecarbon_tracker = None
            except Exception:
                pass

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
    
    end_time = time.time()
    start_time = end_time - duration_seconds
    
    return EnergyRecord(
        start_time=start_time,
        end_time=end_time,
        energy_consumed_kWh=energy_kwh,
        energy_per_token_kWh=energy_per_token,
        estimated=True
    )
