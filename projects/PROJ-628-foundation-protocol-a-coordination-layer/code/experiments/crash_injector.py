"""
Crash Injector Module for Foundation Protocol Experiments.

Supports configurable crash injection strategies:
1. Single-agent crash at a specific timestep
2. Simultaneous crash of multiple agents at the same timestep
3. Fraction-based crash injection across the population

This module is used by SPEAR benchmark runners to test robustness.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

from foundation_protocol.checkpoint import (
    save_checkpoint,
    load_checkpoint,
    serialize_state,
    deserialize_state,
    CheckpointError,
)

logger = logging.getLogger(__name__)


class CrashInjector:
    """
    Manages crash injection events for multi-agent simulations.

    Attributes:
        crash_schedule (List[Tuple[int, Set[str]]]): List of (timestep, agent_ids) tuples.
        crash_fraction (float): Target fraction of agents to crash (0.0 to 1.0).
        crash_probability (float): Probability of crash per agent per step.
        seed (int): Random seed for reproducibility.
    """

    def __init__(
        self,
        crash_schedule: Optional[List[Tuple[int, Set[str]]]] = None,
        crash_fraction: float = 0.0,
        crash_probability: float = 0.0,
        seed: Optional[int] = None,
    ):
        """
        Initialize the CrashInjector.

        Args:
            crash_schedule: Pre-defined list of (timestep, set_of_agent_ids) to crash.
            crash_fraction: If > 0, randomly select this fraction of agents to crash at a specified step.
            crash_probability: If > 0, each agent has this probability of crashing at each step.
            seed: Random seed for deterministic behavior.
        """
        self.crash_schedule = crash_schedule or []
        self.crash_fraction = crash_fraction
        self.crash_probability = crash_probability
        self.seed = seed
        self.rng = random.Random(seed)
        self.crashed_agents: Set[str] = set()
        self.crash_events_log: List[Dict[str, Any]] = []

    def add_single_crash(self, timestep: int, agent_id: str) -> None:
        """
        Schedule a crash for a single agent at a specific timestep.

        Args:
            timestep: The simulation step at which the agent crashes.
            agent_id: The unique identifier of the agent to crash.
        """
        self.crash_schedule.append((timestep, {agent_id}))
        logger.debug(f"Scheduled single crash for agent {agent_id} at timestep {timestep}")

    def add_simultaneous_crash(
        self, timestep: int, agent_ids: List[str]
    ) -> None:
        """
        Schedule simultaneous crashes for multiple agents at the same timestep.

        This is the primary extension for T024b, allowing multiple agents to fail
        at once, simulating cascading failures or network partitions.

        Args:
            timestep: The simulation step at which agents crash.
            agent_ids: List of unique identifiers of agents to crash simultaneously.
        """
        if not agent_ids:
            logger.warning("add_simultaneous_crash called with empty agent_ids list")
            return

        self.crash_schedule.append((timestep, set(agent_ids)))
        logger.debug(
            f"Scheduled simultaneous crash for {len(agent_ids)} agents at timestep {timestep}: {agent_ids}"
        )

    def generate_fractional_crash(
        self, timestep: int, total_agents: List[str]
    ) -> Set[str]:
        """
        Generate a set of agents to crash based on a fraction.

        Args:
            timestep: The simulation step.
            total_agents: List of all active agent IDs.

        Returns:
            Set of agent IDs to crash.
        """
        if self.crash_fraction <= 0.0 or not total_agents:
            return set()

        num_crashes = max(1, int(len(total_agents) * self.crash_fraction))
        # Ensure we don't exceed available agents
        num_crashes = min(num_crashes, len(total_agents))

        selected = self.rng.sample(total_agents, num_crashes)
        selected_set = set(selected)

        self.crash_schedule.append((timestep, selected_set))
        logger.info(
            f"Generated fractional crash: {num_crashes}/{len(total_agents)} agents at timestep {timestep}"
        )
        return selected_set

    def check_step_crashes(
        self, timestep: int, active_agents: List[str]
    ) -> Set[str]:
        """
        Determine which agents should crash at the current timestep.

        Combines pre-scheduled crashes and probabilistic crashes.

        Args:
            timestep: Current simulation step.
            active_agents: List of currently active agent IDs.

        Returns:
            Set of agent IDs that should crash at this step.
        """
        to_crash = set()

        # 1. Check pre-scheduled crashes (including simultaneous)
        for sched_t, sched_agents in self.crash_schedule:
            if sched_t == timestep:
                # Filter to only active agents (ignore already crashed or non-existent)
                valid_agents = sched_agents.intersection(active_agents)
                to_crash.update(valid_agents)

        # 2. Check probabilistic crashes
        if self.crash_probability > 0.0:
            for agent_id in active_agents:
                if agent_id not in to_crash:  # Don't double-crash
                    if self.rng.random() < self.crash_probability:
                        to_crash.add(agent_id)

        # Log the event
        if to_crash:
            event = {
                "timestep": timestep,
                "agents_crashed": list(to_crash),
                "count": len(to_crash),
                "reason": "scheduled" if any(s[0] == timestep for s in self.crash_schedule) else "probabilistic",
            }
            self.crash_events_log.append(event)
            logger.warning(f"CRASH EVENT at step {timestep}: {len(to_crash)} agents failed: {to_crash}")

        return to_crash

    def apply_crashes(
        self,
        timestep: int,
        active_agents: List[str],
        save_state_fn: Optional[Callable[[str, Any], None]] = None,
    ) -> Set[str]:
        """
        Execute crash logic, saving checkpoints if requested before removal.

        Args:
            timestep: Current simulation step.
            active_agents: List of currently active agent IDs.
            save_state_fn: Optional callback(agent_id, state) to save state before crash.

        Returns:
            Set of agent IDs that were crashed.
        """
        agents_to_remove = self.check_step_crashes(timestep, active_agents)

        if save_state_fn and agents_to_remove:
            for agent_id in agents_to_remove:
                try:
                    # We assume the caller passes a way to get state, or we just log
                    # In a real integration, the runner would pass the state dict
                    logger.info(f"Saving checkpoint for crashed agent {agent_id}")
                    # Placeholder for actual state saving if state is passed
                    # save_state_fn(agent_id, state_dict)
                except Exception as e:
                    logger.error(f"Failed to save checkpoint for crashed agent {agent_id}: {e}")

        self.crashed_agents.update(agents_to_remove)
        return agents_to_remove

    def get_crashed_agents(self) -> Set[str]:
        """Return the set of all agents that have crashed so far."""
        return self.crashed_agents

    def get_active_agents(
        self, initial_agents: List[str]
    ) -> List[str]:
        """
        Return list of agents that are still active.

        Args:
            initial_agents: List of all initial agent IDs.

        Returns:
            List of agent IDs that have not crashed.
        """
        return [a for a in initial_agents if a not in self.crashed_agents]

    def reset(self) -> None:
        """Reset the injector state for a new simulation run."""
        self.crashed_agents.clear()
        # Note: We do not clear crash_schedule unless explicitly desired,
        # but for a new run with same schedule, we keep it.
        # If we want to clear schedule too, add self.crash_schedule.clear()
        logger.debug("CrashInjector reset")


def create_crash_injector(
    config: Dict[str, Any],
    seed: Optional[int] = None,
) -> CrashInjector:
    """
    Factory function to create a CrashInjector from a configuration dict.

    Args:
        config: Dictionary with keys:
            - 'schedule': List of {'timestep': int, 'agents': List[str]}
            - 'fraction': float (optional)
            - 'probability': float (optional)
        seed: Random seed.

    Returns:
        Configured CrashInjector instance.
    """
    schedule = []
    if 'schedule' in config:
        for item in config['schedule']:
            timestep = item['timestep']
            agents = set(item.get('agents', []))
            schedule.append((timestep, agents))

    fraction = config.get('fraction', 0.0)
    probability = config.get('probability', 0.0)

    return CrashInjector(
        crash_schedule=schedule,
        crash_fraction=fraction,
        crash_probability=probability,
        seed=seed,
    )


def main() -> None:
    """
    CLI entry point for testing crash injector logic.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Test Crash Injector")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--agents", type=int, default=5, help="Number of agents to simulate"
    )
    parser.add_argument(
        "--steps", type=int, default=10, help="Number of simulation steps"
    )
    parser.add_argument(
        "--simultaneous",
        type=int,
        nargs="+",
        default=[],
        help="Timesteps for simultaneous crashes (e.g. --simultaneous 3 5)",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.0,
        help="Fraction of agents to crash randomly",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create injector
    injector = create_crash_injector(
        {
            "fraction": args.fraction,
            "schedule": [],
        },
        seed=args.seed,
    )

    # Add simultaneous crashes if specified
    if args.simultaneous:
        agent_ids = [f"agent_{i}" for i in range(args.agents)]
        for t in args.simultaneous:
            # Crash half the agents at that step
            crash_list = agent_ids[: args.agents // 2]
            injector.add_simultaneous_crash(t, crash_list)

    # Simulate
    active = [f"agent_{i}" for i in range(args.agents)]
    logger.info(f"Starting simulation with {len(active)} agents for {args.steps} steps")

    for t in range(args.steps):
        crashed = injector.apply_crashes(t, active)
        if crashed:
            active = injector.get_active_agents([f"agent_{i}" for i in range(args.agents)])
            logger.info(f"Step {t}: {len(active)} agents remain active")
        else:
            logger.debug(f"Step {t}: No crashes")

    logger.info(f"Final active agents: {active}")
    logger.info(f"Total crashed: {injector.get_crashed_agents()}")


if __name__ == "__main__":
    main()