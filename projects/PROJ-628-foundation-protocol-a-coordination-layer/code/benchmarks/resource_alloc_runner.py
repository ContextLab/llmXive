"""
Resource Allocation Benchmark Runner (IRM4MLS Simulation)

Implements the Resource Allocation task with detailed byte-level logging
supporting both Foundation Protocol and Native Direct Communication protocols.

This runner simulates N agents competing for limited resources with:
- Configurable resource constraints
- Crash injection support (via crash_injector)
- Foundation Protocol (middleware) vs Native Direct (direct_comm) comparison
- Detailed byte-level communication logging
"""
import json
import os
import random
import time
import logging
import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from pathlib import Path

# Import from foundation_protocol
from foundation_protocol.checkpoint import (
    serialize_state, deserialize_state, save_checkpoint, load_checkpoint,
    create_empty_checkpoint, merge_checkpoints
)
from foundation_protocol.middleware import MessageEnvelope, FoundationMiddleware
from foundation_protocol.direct_comm import DirectCommAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResourceAllocationState:
    """State representation for the resource allocation task."""
    step: int = 0
    total_resources: int = 100
    resources_per_agent: float = 0.0
    agent_demands: List[float] = field(default_factory=list)
    allocations: List[float] = field(default_factory=list)
    crashed_agents: Set[int] = field(default_factory=set)
    completed: bool = False
    success: bool = False
    total_bytes_sent: int = 0
    total_messages: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            'step': self.step,
            'total_resources': self.total_resources,
            'resources_per_agent': self.resources_per_agent,
            'agent_demands': self.agent_demands,
            'allocations': self.allocations,
            'crashed_agents': list(self.crashed_agents),
            'completed': self.completed,
            'success': self.success,
            'total_bytes_sent': self.total_bytes_sent,
            'total_messages': self.total_messages
        }

@dataclass
class ResourceAllocationTask:
    """
    Resource Allocation Task definition.
    
    Simulates N agents competing for limited resources with configurable
    constraints and communication protocols.
    """
    n_agents: int
    total_resources: float
    resource_constraints: Dict[str, Any] = field(default_factory=dict)
    episode_length: int = 50
    seed: int = 42
    
    def __post_init__(self):
        random.seed(self.seed)
        self.state = ResourceAllocationState(
            total_resources=int(self.total_resources),
            agent_demands=[random.uniform(0.5, 1.5) for _ in range(self.n_agents)],
            allocations=[0.0] * self.n_agents
        )
    
    def reset(self) -> ResourceAllocationState:
        """Reset the task state."""
        random.seed(self.seed)
        self.state = ResourceAllocationState(
            total_resources=int(self.total_resources),
            agent_demands=[random.uniform(0.5, 1.5) for _ in range(self.n_agents)],
            allocations=[0.0] * self.n_agents
        )
        return self.state
    
    def step(
        self, 
        agent_actions: List[Dict[str, Any]], 
        crash_injector: Optional[Any] = None
    ) -> Tuple[ResourceAllocationState, Dict[str, Any]]:
        """
        Execute one step of the resource allocation task.
        
        Args:
            agent_actions: List of actions from each agent
            crash_injector: Optional crash injector for failure simulation
        
        Returns:
            Tuple of (new_state, info_dict)
        """
        self.state.step += 1
        
        # Handle crash injection if provided
        if crash_injector:
            crashed = crash_injector.get_crashed_agents(self.state.step)
            self.state.crashed_agents = crashed
        
        # Calculate resource requests and allocations
        total_requested = 0.0
        requests = []
        
        for i, action in enumerate(agent_actions):
            if i in self.state.crashed_agents:
                # Crashed agents make no request
                requests.append(0.0)
                continue
            
            demand = self.state.agent_demands[i]
            request = action.get('resource_request', demand)
            requests.append(request)
            total_requested += request
        
        # Allocate resources proportionally
        available = self.state.total_resources
        for i, request in enumerate(requests):
            if i in self.state.crashed_agents:
                self.state.allocations[i] = 0.0
            elif total_requested > 0:
                self.state.allocations[i] = (request / total_requested) * available
            else:
                self.state.allocations[i] = available / self.n_agents
        
        # Update resources per agent
        self.state.resources_per_agent = sum(self.state.allocations) / self.n_agents
        
        # Check completion
        if self.state.step >= self.episode_length:
            self.state.completed = True
            # Success if all agents got at least 80% of their demand
            success = all(
                self.state.allocations[i] >= 0.8 * self.state.agent_demands[i]
                for i in range(self.n_agents)
                if i not in self.state.crashed_agents
            )
            self.state.success = success
        
        info = {
            'step': self.state.step,
            'total_requested': total_requested,
            'total_allocated': sum(self.state.allocations),
            'crashed_count': len(self.state.crashed_agents)
        }
        
        return self.state, info

class IRM4MLSRunner:
    """
    IRM4MLS Resource Allocation Runner.
    
    Supports both Foundation Protocol (middleware) and Native Direct
    Communication protocols with detailed byte-level logging.
    """
    
    def __init__(
        self,
        task: ResourceAllocationTask,
        protocol: str = 'foundation',
        crash_injector: Optional[Any] = None,
        checkpoint_dir: Optional[str] = None
    ):
        """
        Initialize the runner.
        
        Args:
            task: ResourceAllocationTask instance
            protocol: 'foundation' or 'direct'
            crash_injector: Optional crash injector
            checkpoint_dir: Directory for checkpointing
        """
        self.task = task
        self.protocol = protocol
        self.crash_injector = crash_injector
        self.checkpoint_dir = checkpoint_dir
        
        # Initialize agents based on protocol
        self.agents = []
        if protocol == 'foundation':
            for i in range(task.n_agents):
                agent = FoundationMiddleware(
                    agent_id=i,
                    checkpoint_dir=checkpoint_dir
                )
                self.agents.append(agent)
        else:
            for i in range(task.n_agents):
                agent = DirectCommAgent(
                    agent_id=i,
                    checkpoint_dir=checkpoint_dir
                )
                self.agents.append(agent)
        
        # Metrics tracking
        self.metrics = {
            'episode_length': 0,
            'msg_count': 0,
            'bytes_sent': 0,
            'recovery_success': False,
            'recovery_latency': 0.0,
            'task_success': False,
            'protocol': protocol,
            'seed': task.seed,
            'n_agents': task.n_agents
        }
        
        # Byte-level logging
        self.byte_log: List[Dict[str, Any]] = []
    
    def _log_message_bytes(
        self, 
        sender_id: int, 
        receiver_id: int, 
        payload: Any,
        protocol_type: str
    ) -> int:
        """
        Log message transmission with byte-level detail.
        
        Args:
            sender_id: ID of sending agent
            receiver_id: ID of receiving agent
            payload: Message payload
            protocol_type: 'foundation' or 'direct'
        
        Returns:
            Number of bytes sent
        """
        # Serialize payload to estimate size
        payload_str = json.dumps(payload) if not isinstance(payload, str) else payload
        byte_size = len(payload_str.encode('utf-8'))
        
        # Add protocol overhead
        if protocol_type == 'foundation':
            # Foundation Protocol adds envelope overhead
            envelope = {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'timestamp': time.time(),
                'payload_size': byte_size,
                'signature': hashlib.sha256(payload_str.encode()).hexdigest()[:64]
            }
            envelope_str = json.dumps(envelope)
            total_bytes = len(envelope_str.encode('utf-8'))
        else:
            # Direct communication: just the payload
            total_bytes = byte_size
        
        # Log the transmission
        self.byte_log.append({
            'step': self.task.state.step,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'payload_size': byte_size,
            'total_bytes': total_bytes,
            'protocol': protocol_type,
            'timestamp': time.time()
        })
        
        return total_bytes
    
    def run_episode(self) -> Dict[str, Any]:
        """
        Run a complete episode of the resource allocation task.
        
        Returns:
            Dictionary with episode metrics and byte-level logs
        """
        self.task.reset()
        episode_start = time.time()
        
        for step in range(self.task.episode_length):
            # Check for crashes
            if self.crash_injector:
                crashed = self.crash_injector.get_crashed_agents(step)
                self.task.state.crashed_agents = crashed
            
            # Generate actions from agents
            actions = []
            for i, agent in enumerate(self.agents):
                if i in self.task.state.crashed_agents:
                    # Crashed agent sends no message
                    actions.append({})
                    continue
                
                # Agent decides on resource request
                # For simulation, agents request based on their demand
                action = {'resource_request': self.task.agent_demands[i]}
                
                # Simulate inter-agent communication
                # Each agent broadcasts to all others (simplified model)
                for j in range(self.task.n_agents):
                    if i != j and j not in self.task.state.crashed_agents:
                        msg_payload = {
                            'agent_id': i,
                            'request': action['resource_request'],
                            'step': step
                        }
                        
                        bytes_sent = self._log_message_bytes(
                            sender_id=i,
                            receiver_id=j,
                            payload=msg_payload,
                            protocol_type=self.protocol
                        )
                        
                        self.metrics['bytes_sent'] += bytes_sent
                        self.metrics['msg_count'] += 1
                
                actions.append(action)
            
            # Execute task step
            state, info = self.task.step(actions, self.crash_injector)
            
            # Checkpoint if configured
            if self.checkpoint_dir and step % 10 == 0:
                checkpoint_data = {
                    'state': state.to_dict(),
                    'metrics': self.metrics,
                    'step': step
                }
                save_checkpoint(
                    checkpoint_data,
                    Path(self.checkpoint_dir) / f"checkpoint_{step}.json"
                )
            
            # Check if episode ended
            if state.completed:
                break
        
        episode_end = time.time()
        self.metrics['episode_length'] = step + 1
        self.metrics['task_success'] = state.success
        self.metrics['recovery_success'] = len(state.crashed_agents) < self.task.n_agents
        self.metrics['recovery_latency'] = episode_end - episode_start
        
        return {
            'metrics': self.metrics,
            'byte_log': self.byte_log,
            'final_state': state.to_dict()
        }

def run_resource_allocation_benchmark(
    n_agents: int = 5,
    total_resources: float = 100.0,
    episode_length: int = 50,
    n_seeds: int = 10,
    protocol: str = 'foundation',
    crash_fraction: float = 0.0,
    checkpoint_dir: Optional[str] = None,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Run the resource allocation benchmark with multiple seeds.
    
    Args:
        n_agents: Number of agents
        total_resources: Total available resources
        episode_length: Maximum episode length
        n_seeds: Number of seeds to run
        protocol: 'foundation' or 'direct'
        crash_fraction: Fraction of agents to crash (0.0-1.0)
        checkpoint_dir: Optional checkpoint directory
        seed: Optional base seed for reproducibility
    
    Returns:
        List of episode results with metrics and byte logs
    """
    results = []
    
    # Import crash injector if needed
    crash_injector = None
    if crash_fraction > 0.0:
        from experiments.crash_injector import create_crash_injector
        crash_injector = create_crash_injector(
            n_agents=n_agents,
            crash_fraction=crash_fraction,
            mode='random'
        )
    
    for i in range(n_seeds):
        if seed is not None:
            task_seed = seed + i
        else:
            task_seed = random.randint(0, 1000000)
        
        logger.info(f"Running seed {task_seed} with protocol {protocol}")
        
        task = ResourceAllocationTask(
            n_agents=n_agents,
            total_resources=total_resources,
            episode_length=episode_length,
            seed=task_seed
        )
        
        runner = IRM4MLSRunner(
            task=task,
            protocol=protocol,
            crash_injector=crash_injector,
            checkpoint_dir=checkpoint_dir
        )
        
        result = runner.run_episode()
        results.append(result)
        
        logger.info(f"Seed {task_seed} complete: "
                    f"success={result['metrics']['task_success']}, "
                    f"msg_count={result['metrics']['msg_count']}, "
                    f"bytes={result['metrics']['bytes_sent']}")
    
    return results

def main():
    """Main entry point for the resource allocation benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resource Allocation Benchmark')
    parser.add_argument('--n-agents', type=int, default=5, help='Number of agents')
    parser.add_argument('--total-resources', type=float, default=100.0, help='Total resources')
    parser.add_argument('--episode-length', type=int, default=50, help='Episode length')
    parser.add_argument('--n-seeds', type=int, default=3, help='Number of seeds')
    parser.add_argument('--protocol', type=str, default='foundation', 
                      choices=['foundation', 'direct'], help='Communication protocol')
    parser.add_argument('--crash-fraction', type=float, default=0.0, help='Crash fraction')
    parser.add_argument('--output-dir', type=str, default='data', help='Output directory')
    parser.add_argument('--seed', type=int, default=None, help='Base seed')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run benchmark
    results = run_resource_allocation_benchmark(
        n_agents=args.n_agents,
        total_resources=args.total_resources,
        episode_length=args.episode_length,
        n_seeds=args.n_seeds,
        protocol=args.protocol,
        crash_fraction=args.crash_fraction,
        checkpoint_dir=str(output_dir / 'checkpoints'),
        seed=args.seed
    )
    
    # Save results
    output_file = output_dir / f"resource_alloc_{args.protocol}_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Print summary
    for i, result in enumerate(results):
        m = result['metrics']
        print(f"Seed {i}: success={m['task_success']}, "
              f"msg_count={m['msg_count']}, "
              f"bytes_sent={m['bytes_sent']}")

if __name__ == '__main__':
    main()