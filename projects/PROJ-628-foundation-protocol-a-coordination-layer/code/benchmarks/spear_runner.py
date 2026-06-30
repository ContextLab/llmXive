import os
import sys
import json
import random
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import shared checkpoint logic
from foundation_protocol.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    serialize_state,
    deserialize_state,
    create_empty_checkpoint
)
from foundation_protocol.middleware import FoundationMiddleware
from foundation_protocol.direct_comm import DirectCommAgent
from experiments.crash_injector import CrashInjector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SPEARState:
    """State representation for the SPEAR benchmark environment."""
    current_step: int = 0
    total_agents: int = 0
    active_agents: int = 0
    crashed_agents: List[int] = field(default_factory=list)
    recovered_agents: List[int] = field(default_factory=list)
    current_resources: Dict[int, float] = field(default_factory=dict)
    task_progress: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class SPEARMetricRecord:
    """
    MetricRecord for SPEAR benchmark.
    Extends the base MetricRecord with recovery-specific fields.
    """
    seed: int
    protocol: str  # 'Foundation' or 'NativeDirect'
    episode_length: int
    msg_count: int
    bytes_sent: int
    recovery_success: bool
    recovery_latency: float  # Time in seconds to recover from crash
    task_success: bool
    # Additional SPEAR specific metrics
    crash_injection_step: Optional[int] = None
    total_crashes: int = 0
    total_recoveries: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SPEAREnvironment:
    """
    Simulation environment for the SPEAR benchmark (Smart Contract Auditing Workflow).
    Simulates agent interactions, resource constraints, and crash scenarios.
    """
    def __init__(self, num_agents: int, seed: int, crash_injector: Optional[CrashInjector] = None):
        self.num_agents = num_agents
        self.seed = seed
        self.crash_injector = crash_injector
        self.state = SPEARState(
            current_step=0,
            total_agents=num_agents,
            active_agents=num_agents,
            crashed_agents=[],
            recovered_agents=[]
        )
        # Initialize resources
        self.state.current_resources = {i: 1.0 for i in range(num_agents)}
        random.seed(seed)

    def step(self, protocol: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute one step of the simulation.
        Returns (done, metrics)
        """
        self.state.current_step += 1
        step_metrics = {
            'msg_count': 0,
            'bytes_sent': 0
        }

        # Check for crash injection
        if self.crash_injector:
            crash_info = self.crash_injector.check_for_crash(self.state.current_step, self.state.active_agents)
            if crash_info:
                self._handle_crash(crash_info)

        # Simulate agent actions based on protocol
        if protocol == "Foundation":
            # Foundation Protocol logic with middleware
            success, step_metrics = self._run_foundation_step()
        else:
            # Native Direct Communication
            success, step_metrics = self._run_direct_step()

        # Update task progress (simplified model)
        self.state.task_progress += 0.05  # 5% per step
        if self.state.task_progress >= 1.0:
            self.state.task_progress = 1.0
            return True, step_metrics

        return False, step_metrics

    def _run_foundation_step(self) -> Tuple[bool, Dict[str, Any]]:
        """Simulate Foundation Protocol step with middleware overhead."""
        msg_count = 0
        bytes_sent = 0
        # Simulate message passing
        active_ids = [i for i in range(self.num_agents) if i not in self.state.crashed_agents]
        if len(active_ids) < 2:
            return False, {'msg_count': 0, 'bytes_sent': 0}

        # Each active agent sends a message to a random peer
        for agent_id in active_ids:
            target = random.choice([x for x in active_ids if x != agent_id])
            msg_count += 1
            bytes_sent += 64  # Simulated payload size

        return True, {'msg_count': msg_count, 'bytes_sent': bytes_sent}

    def _run_direct_step(self) -> Tuple[bool, Dict[str, Any]]:
        """Simulate Native Direct Communication step."""
        msg_count = 0
        bytes_sent = 0
        active_ids = [i for i in range(self.num_agents) if i not in self.state.crashed_agents]
        if len(active_ids) < 2:
            return False, {'msg_count': 0, 'bytes_sent': 0}

        for agent_id in active_ids:
            target = random.choice([x for x in active_ids if x != agent_id])
            msg_count += 1
            bytes_sent += 64

        return True, {'msg_count': msg_count, 'bytes_sent': bytes_sent}

    def _handle_crash(self, crash_info: Dict[str, Any]):
        """Handle agent crash and initiate recovery if configured."""
        crash_agent = crash_info['agent_id']
        self.state.crashed_agents.append(crash_agent)
        self.state.active_agents -= 1
        logger.info(f"Agent {crash_agent} crashed at step {self.state.current_step}")

        # Check if recovery is triggered
        if self.crash_injector and self.crash_injector.should_attempt_recovery():
            self._attempt_recovery(crash_agent)

    def _attempt_recovery(self, agent_id: int):
        """Attempt to recover a crashed agent."""
        start_time = time.time()
        # Simulate recovery logic (checkpoint restore, state re-sync)
        # In a real scenario, this would involve loading state from checkpoint
        success = random.random() > 0.1  # 90% success rate
        recovery_time = time.time() - start_time

        if success:
            self.state.crashed_agents.remove(agent_id)
            self.state.recovered_agents.append(agent_id)
            self.state.active_agents += 1
            logger.info(f"Agent {agent_id} recovered in {recovery_time:.4f}s")
        else:
            logger.warning(f"Agent {agent_id} recovery failed")

    def get_state(self) -> SPEARState:
        return self.state

class SPEARAgent:
    """
    Agent wrapper for the SPEAR benchmark.
    Handles communication and state management.
    """
    def __init__(self, agent_id: int, protocol: str, env: SPEAREnvironment):
        self.agent_id = agent_id
        self.protocol = protocol
        self.env = env
        self.checkpoint_data = {}

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform an action based on observation."""
        # Simplified action logic
        return {'action': 'audit', 'confidence': random.uniform(0.8, 1.0)}

    def save_checkpoint(self, step: int):
        """Save current state to checkpoint."""
        state = {
            'agent_id': self.agent_id,
            'step': step,
            'protocol': self.protocol,
            'data': self.checkpoint_data
        }
        # In a real implementation, this would call save_checkpoint from checkpoint.py
        # For simulation, we just store it in memory
        self.checkpoint_data = state

    def load_checkpoint(self, step: int):
        """Load state from checkpoint."""
        if self.checkpoint_data.get('step') == step:
            return self.checkpoint_data
        return None

def run_spear_benchmark(
    seed: int,
    protocol: str,
    num_agents: int = 5,
    crash_injector: Optional[CrashInjector] = None,
    output_path: Optional[str] = None
) -> SPEARMetricRecord:
    """
    Run the SPEAR benchmark for a single seed and protocol.

    Args:
        seed: Random seed for reproducibility
        protocol: 'Foundation' or 'NativeDirect'
        num_agents: Number of agents in the simulation
        crash_injector: Optional crash injector for fault tolerance testing
        output_path: Optional path to save the result

    Returns:
        SPEARMetricRecord containing the benchmark results
    """
    random.seed(seed)
    env = SPEAREnvironment(num_agents=num_agents, seed=seed, crash_injector=crash_injector)

    total_msg_count = 0
    total_bytes_sent = 0
    episode_length = 0
    start_time = time.time()
    recovery_start_time = None
    recovery_latency = 0.0
    recovered_agents = 0

    done = False
    step = 0
    while not done:
        step += 1
        episode_length = step
        success, step_metrics = env.step(protocol)
        total_msg_count += step_metrics['msg_count']
        total_bytes_sent += step_metrics['bytes_sent']

        # Track recovery latency if a crash occurred
        if env.state.crashed_agents and not env.state.recovered_agents:
            if recovery_start_time is None:
                recovery_start_time = time.time()
        elif env.state.recovered_agents and recovery_start_time is not None:
            # Calculate latency for the last recovery event
            recovery_latency = time.time() - recovery_start_time
            recovered_agents = len(env.state.recovered_agents)
            recovery_start_time = None

    end_time = time.time()
    total_time = end_time - start_time

    # Determine success metrics
    # Task success: completed the workflow (progress >= 1.0)
    task_success = env.state.task_progress >= 1.0
    # Recovery success: all crashed agents were recovered (if any crashes occurred)
    if env.state.crashed_agents:
        recovery_success = len(env.state.recovered_agents) == len(env.state.crashed_agents)
    else:
        recovery_success = True  # No crashes, so trivially successful

    record = SPEARMetricRecord(
        seed=seed,
        protocol=protocol,
        episode_length=episode_length,
        msg_count=total_msg_count,
        bytes_sent=total_bytes_sent,
        recovery_success=recovery_success,
        recovery_latency=recovery_latency,
        task_success=task_success,
        crash_injection_step=env.state.crash_injector.crash_step if env.state.crash_injector else None,
        total_crashes=len(env.state.crashed_agents),
        total_recoveries=len(env.state.recovered_agents),
        timestamp=datetime.now().isoformat()
    )

    if output_path:
        with open(output_path, 'w') as f:
            json.dump(record.to_dict(), f, indent=2)

    return record

def main():
    """Entry point for running the SPEAR benchmark."""
    import argparse
    parser = argparse.ArgumentParser(description="Run SPEAR Benchmark")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--protocol", type=str, default="Foundation", choices=["Foundation", "NativeDirect"])
    parser.add_argument("--agents", type=int, default=5, help="Number of agents")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    args = parser.parse_args()

    logger.info(f"Running SPEAR benchmark: seed={args.seed}, protocol={args.protocol}, agents={args.agents}")
    record = run_spear_benchmark(
        seed=args.seed,
        protocol=args.protocol,
        num_agents=args.agents,
        output_path=args.output
    )
    print(json.dumps(record.to_dict(), indent=2))

if __name__ == "__main__":
    main()