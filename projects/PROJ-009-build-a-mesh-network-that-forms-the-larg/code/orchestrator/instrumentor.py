from __future__ import annotations
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from orchestrator.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PacketStats:
    total_packets: int
    packets_per_second: float
    lost_packets: int
    loss_rate: float

@dataclass
class CPUStats:
    cpu_utilization_pct: float
    user_pct: float
    system_pct: float
    idle_pct: float
    iowait_pct: float

@dataclass
class NodeMetrics:
    node_id: str
    timestamp: float
    packet_stats: Optional[PacketStats]
    cpu_stats: Optional[CPUStats]

class Instrumentor:
    """Local instrumentor for testing or non-remote scenarios."""
    
    def __init__(self):
        self.logger = get_logger(__name__)

    def parse_tcpdump_output(self, output: str, expected_count: int = 1000) -> PacketStats:
        """Parse tcpdump output string."""
        captured_match = re.search(r'(\d+)\s+packets?\s+captured', output)
        if captured_match:
            captured = int(captured_match.group(1))
        else:
            captured = 0
        
        lost = max(0, expected_count - captured)
        loss_rate = lost / expected_count if expected_count > 0 else 0.0
        pps = captured / 1.0 # Placeholder duration
        
        return PacketStats(
            total_packets=captured,
            packets_per_second=pps,
            lost_packets=lost,
            loss_rate=loss_rate
        )

    def parse_mpstat_output(self, output: str) -> CPUStats:
        """Parse mpstat output string."""
        lines = output.strip().split('\n')
        avg_idle = 0.0
        count = 0
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 12 and parts[0] != "Average:":
                try:
                    idle_str = parts[-1]
                    idle = float(idle_str)
                    avg_idle += idle
                    count += 1
                except (ValueError, IndexError):
                    continue
        
        if count > 0:
            avg_idle /= count
        
        utilization = 100.0 - avg_idle
        
        return CPUStats(
            cpu_utilization_pct=utilization,
            user_pct=0.0, # Simplified
            system_pct=0.0,
            idle_pct=avg_idle,
            iowait_pct=0.0
        )

    def check_network_saturation(self, packet_stats: PacketStats, threshold: float = 0.20) -> bool:
        return packet_stats.loss_rate > threshold

def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Local Instrumentor module loaded.")

if __name__ == "__main__":
    main()
