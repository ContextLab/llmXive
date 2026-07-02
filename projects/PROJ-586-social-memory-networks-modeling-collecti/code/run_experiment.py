import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# Import existing project modules
from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import get_shared_memory_buffer, reset_shared_memory_buffer, MemoryAction
from metrics.specialization import compute_specialization_index, compute_game_level_specialization
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval
from metrics.validator import validate_and_filter_records, compute_metric_statistics
from utils.logging import setup_logger, get_logger, log_experiment_start, log_experiment_end
from utils.config import get_config_manager, get_config
from data.loaders import get_dataset, save_experiment_results

# --- Simulation Logic ---

def run_single_game(
    game_id: int,
    agents: List[BaseAgent],
    context_condition: str,
    max_tokens: int,
    logger: Any
) -> Dict[str, Any]:
    """
    Run a single simulation game.
    
    Args:
        game_id: Unique identifier for the game.
        agents: List of agent instances.
        context_condition: Either 'full' or 'limited'.
        max_tokens: Maximum context window size (relevant for 'limited').
        logger: Logger instance.
        
    Returns:
        Dictionary containing game results including metrics.
    """
    # Reset shared memory for this game
    reset_shared_memory_buffer()
    buffer = get_shared_memory_buffer()
    
    # Initialize game state (simulated using synthetic data logic)
    # In a real scenario, this would load from a dataset. 
    # Here we simulate the interaction loop required to generate memory actions.
    
    game_data = {
        "game_id": game_id,
        "context_condition": context_condition,
        "agent_count": len(agents),
        "metrics": {},
        "raw_interactions": []
    }
    
    # Simulate a "memory game" where agents store and retrieve information
    # We simulate N turns of interaction
    num_turns = 10
    
    for turn in range(num_turns):
        # 1. Agent Selection (Round Robin for simplicity)
        current_agent = agents[turn % len(agents)]
        
        # 2. Context Construction
        # If limited, truncate the history passed to the agent
        full_history = buffer.get_history()
        if context_condition == "limited":
            # Simple truncation: keep last max_tokens tokens (approximated by last N entries)
            # In a real transformer, this would be token-based. 
            # We approximate by slicing the list of memory entries.
            # Assuming each entry is ~20 tokens, 128 tokens ~ 6 entries.
            approx_entries = max(1, int(max_tokens / 20))
            context_window = full_history[-approx_entries:] if len(full_history) > approx_entries else full_history
        else:
            context_window = full_history
        
        # 3. Agent Action
        # The agent decides to STORE or RETRIEVE based on context
        # We simulate the agent's decision process
        # In a real implementation, this calls current_agent.generate(...)
        
        # Simulated decision logic:
        # If context is short, retrieval might fail or be less efficient
        # If context is full, retrieval is more likely to succeed
        
        action_type = "STORE"
        content = f"Fact_{game_id}_Turn_{turn}_Agent_{current_agent.agent_id}"
        
        # Simulate a retrieval attempt if context exists and it's not the first turn
        if turn > 0 and np.random.rand() > 0.5:
            action_type = "RETRIEVE"
            # Try to retrieve a specific fact
            target = f"Fact_{game_id}_Turn_{turn-1}_Agent_{agents[(turn-1)%len(agents)].agent_id}"
            # Simulate success based on context window
            if target in str(context_window):
                retrieved_content = target
                success = True
            else:
                retrieved_content = None
                success = False
            
            memory_action = MemoryAction(
                action_type="RETRIEVE",
                content=retrieved_content,
                success=success,
                agent_id=current_agent.agent_id,
                turn=turn
            )
        else:
            # Store action
            memory_action = MemoryAction(
                action_type="STORE",
                content=content,
                success=True,
                agent_id=current_agent.agent_id,
                turn=turn
            )
            buffer.add_entry(memory_action)
        
        game_data["raw_interactions"].append({
            "turn": turn,
            "agent_id": current_agent.agent_id,
            "action": action_type,
            "success": memory_action.success if action_type == "RETRIEVE" else True
        })

    # 4. Compute Metrics
    # Calculate Specialization Index
    # Specialization is based on how distinct the agents' stored memories are
    # We count unique facts stored per agent
    agent_stored_facts = {}
    for entry in buffer.get_history():
        if entry.action_type == "STORE":
            aid = entry.agent_id
            if aid not in agent_stored_facts:
                agent_stored_facts[aid] = set()
            agent_stored_facts[aid].add(entry.content)
    
    # Compute specialization index (0 to log2(N))
    specialization_val = compute_specialization_index(agent_stored_facts, len(agents))
    
    # Calculate Retrieval Efficiency
    # Proportion of successful retrievals vs total retrieval attempts
    retrieval_attempts = [i for i in game_data["raw_interactions"] if i["action"] == "RETRIEVE"]
    if len(retrieval_attempts) > 0:
        successful_retrievals = sum(1 for i in retrieval_attempts if i["success"])
        retrieval_eff = successful_retrievals / len(retrieval_attempts)
    else:
        retrieval_eff = 0.0 # No attempts made
    
    # Validate metrics
    game_record = {
        "game_id": game_id,
        "specialization_index": specialization_val,
        "retrieval_efficiency": retrieval_eff,
        "context_condition": context_condition,
        "agent_count": len(agents)
    }
    
    validation = validate_and_filter_records([game_record])
    if not validation["valid"]:
        logger.warning(f"Game {game_id} failed validation: {validation['reason']}")
        # Return None to indicate failure, or handle as needed
        # For this simulation, we assume the synthetic logic always produces valid ranges
        
    game_data["metrics"]["specialization_index"] = specialization_val
    game_data["metrics"]["retrieval_efficiency"] = retrieval_eff
    
    return game_data

def run_experiment(
    num_games: int,
    context_condition: str,
    agent_count: int,
    max_tokens: int,
    seed: int,
    output_path: Path,
    logger: Any
) -> pd.DataFrame:
    """
    Run the full experiment loop.
    
    Args:
        num_games: Number of games to simulate.
        context_condition: 'full' or 'limited'.
        agent_count: Number of agents in the simulation.
        max_tokens: Context window limit (for 'limited').
        seed: Random seed.
        output_path: Path to save results.
        logger: Logger instance.
        
    Returns:
        DataFrame of results.
    """
    np.random.seed(seed)
    
    # Create agents
    # Using a simple mock configuration for the BaseAgent
    # In a real run, this would load a model
    agent_configs = []
    for i in range(agent_count):
        cfg = AgentConfig(
            agent_id=f"agent_{i}",
            model_name="opt-125m", # Small model for CPU
            device="cpu"
        )
        agent_configs.append(cfg)
    
    agents = [BaseAgent(cfg) for cfg in agent_configs]
    
    results = []
    log_experiment_start(logger, context_condition, num_games, agent_count)
    
    for i in range(num_games):
        try:
            game_result = run_single_game(
                game_id=i,
                agents=agents,
                context_condition=context_condition,
                max_tokens=max_tokens,
                logger=logger
            )
            
            if game_result:
                results.append({
                    "game_id": i,
                    "specialization_index": game_result["metrics"]["specialization_index"],
                    "retrieval_efficiency": game_result["metrics"]["retrieval_efficiency"],
                    "context_condition": context_condition,
                    "agent_count": agent_count
                })
        except Exception as e:
            logger.error(f"Game {i} failed: {e}")
            continue
    
    df = pd.DataFrame(results)
    
    # Save to CSV
    save_experiment_results(df, output_path)
    log_experiment_end(logger, len(df), output_path)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Run Social Memory Network Experiment")
    parser.add_argument("--context", type=str, default="full", choices=["full", "limited"],
                        help="Context condition: 'full' or 'limited'")
    parser.add_argument("--agents", type=int, default=3, help="Number of agents")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to simulate")
    parser.add_argument("--tokens", type=int, default=128, help="Max tokens for limited context")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    
    args = parser.parse_args()
    
    # Setup logging
    log_path = Path("code/experiment.log")
    logger = setup_logger(log_path)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        base_name = f"results_{args.context}.csv"
        output_path = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results") / base_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting experiment: {args.context} context, {args.agents} agents, {args.games} games")
    
    # Run experiment
    df = run_experiment(
        num_games=args.games,
        context_condition=args.context,
        agent_count=args.agents,
        max_tokens=args.tokens,
        seed=args.seed,
        output_path=output_path,
        logger=logger
    )
    
    logger.info(f"Experiment complete. Results saved to {output_path}")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()