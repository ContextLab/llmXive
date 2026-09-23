import json
import os
import sys
import argparse
from pathlib import Path
from itertools import islice

try:
    import gymnasium as gym
    from minigrid.wrappers import ImgObsWrapper
    from minigrid.envs import MiniGridEnv
    HAS_MINIGRID = True
except ImportError:
    HAS_MINIGRID = False
    print("Warning: minigrid not installed. MiniGrid path generation will be skipped.", file=sys.stderr)

try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("Warning: datasets not installed. GSM8K path generation will be skipped.", file=sys.stderr)

def generate_minigrid_paths(seed: int, map_id: str, output_path: Path) -> None:
    """
    Generates valid shortest paths for a specific MiniGrid configuration.
    Uses BFS to find all shortest paths from start to goal.
    """
    if not HAS_MINIGRID:
        raise RuntimeError("minigrid library is required to generate MiniGrid paths.")

    # Construct environment
    # Note: map_id usually refers to the seed or a specific grid string in MiniGrid contexts.
    # We assume map_id here acts as the seed for the procedural generation if not a static string.
    # If map_id is a static grid string, we would pass it to the env constructor.
    # For this implementation, we treat map_id as a seed for procedural generation of a standard size.
    
    env = gym.make('MiniGrid-Empty-8x8-v0')
    env.reset(seed=seed)
    
    # In a real scenario, we would parse map_id if it's a grid string.
    # Since we need to generate paths based on seed and map_id, we assume the environment
    # is configured such that seed+map_id defines the start/goal.
    
    start_pos = env.unwrapped.agent_pos
    start_dir = env.unwrapped.agent_dir
    goal_pos = env.unwrapped.grid.find('goal')
    
    if goal_pos is None:
        # If no goal found in default env, we might need to parse map_id as a grid string.
        # For robustness, we assume standard empty room or parse map_id.
        # If map_id is a seed for a different map type, we'd need more logic.
        # Here we assume standard Empty-8x8 for demonstration of the BFS logic.
        # In a real pipeline, map_id would likely be passed to the env constructor.
        raise ValueError(f"Could not locate goal in environment generated with seed={seed}.")

    # BFS to find all shortest paths
    # State: (pos, dir) -> but for path validity in MiniGrid, we usually care about the sequence of actions or positions.
    # The task asks for "valid_paths" as List[str]. We will represent paths as comma-separated coordinates.
    
    from collections import deque, defaultdict

    queue = deque([(start_pos, [])])
    visited = {start_pos}
    shortest_len = None
    all_shortest_paths = []

    while queue:
        (pos, path) = queue.popleft()
        
        if shortest_len is not None and len(path) >= shortest_len:
            continue

        if pos == goal_pos:
            if shortest_len is None:
                shortest_len = len(path)
                all_shortest_paths.append(path)
            elif len(path) == shortest_len:
                all_shortest_paths.append(path)
            continue

        # Try all 4 directions
        for d in range(4):
            # Calculate new position
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][d]
            new_pos = (pos[0] + dx, pos[1] + dy)
            
            # Check bounds and walls
            if 0 <= new_pos[0] < env.unwrapped.grid.width and 0 <= new_pos[1] < env.unwrapped.grid.height:
                cell = env.unwrapped.grid.get(new_pos[0], new_pos[1])
                if cell is None or (cell.type == 'goal'): # Empty or Goal
                    if new_pos not in visited:
                        visited.add(new_pos)
                        new_path = path + [new_pos]
                        queue.append((new_pos, new_path))
    
    # Format paths as strings: "x,y;x,y;..."
    formatted_paths = []
    for p in all_shortest_paths:
        formatted_paths.append(";".join([f"{x},{y}" for x, y in p]))

    record = {
        "prompt_id": f"minigrid_{seed}_{map_id}",
        "task_type": "minigrid",
        "valid_paths": formatted_paths,
        "seed": seed,
        "map_id": map_id
    }

    with open(output_path, 'a') as f:
        f.write(json.dumps(record) + '\n')

def fetch_gsm8k_ground_truth(output_path: Path, limit: int = 500) -> None:
    """
    Fetches GSM8K ground truth solutions.
    For GSM8K, the "valid path" is the solution string provided in the dataset.
    """
    if not HAS_DATASETS:
        raise RuntimeError("datasets library is required to fetch GSM8K.")

    ds = load_dataset("gsm8k", "main", split="train", streaming=True)
    
    count = 0
    with open(output_path, 'a') as f:
        for item in islice(ds, limit):
            # GSM8K fields: question, answer
            # We extract the final answer as the valid path
            prompt_id = item.get('question', '')[:20] # Truncate for ID
            answer = item.get('answer', '')
            
            # The answer usually contains the reasoning and the final answer.
            # We store the full answer string as the valid path for semantic alignment.
            record = {
                "prompt_id": f"gsm8k_{count}",
                "task_type": "gsm8k",
                "valid_paths": [answer],
                "seed": 42, # Static seed for GSM8K as it's a static dataset
                "map_id": "gsm8k_main"
            }
            f.write(json.dumps(record) + '\n')
            count += 1

def fetch_minigrid_ground_truth(output_path: Path, seeds: list = None, limit: int = 500) -> None:
    """
    Generates ground truth paths for MiniGrid by running the environment.
    """
    if not seeds:
        seeds = list(range(limit))
    
    for i, seed in enumerate(seeds):
        if i >= limit:
            break
        # We use a generic map_id or derive from seed if needed.
        # Here we assume a standard map generation based on seed.
        map_id = f"seed_{seed}"
        generate_minigrid_paths(seed, map_id, output_path)

def main():
    parser = argparse.ArgumentParser(description="Generate ground truth paths for GSM8K and MiniGrid.")
    parser.add_argument('--output', type=str, default='data/ground_truth_paths.jsonl',
                        help='Output file path for the generated JSONL data.')
    parser.add_argument('--task', type=str, choices=['gsm8k', 'minigrid', 'all'], default='all',
                        help='Which task to generate data for.')
    parser.add_argument('--seed', type=int, default=None,
                        help='Specific seed for MiniGrid generation.')
    parser.add_argument('--map-id', type=str, default=None,
                        help='Specific map ID for MiniGrid generation.')
    parser.add_argument('--limit', type=int, default=500,
                        help='Number of examples to generate/fetch.')
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear file if it exists to avoid appending to old runs
    if output_path.exists():
        output_path.unlink()
    
    # Create empty file
    output_path.touch()

    if args.task in ['gsm8k', 'all']:
        print(f"Fetching GSM8K ground truth (limit={args.limit})...")
        try:
            fetch_gsm8k_ground_truth(output_path, limit=args.limit)
            print(f"Completed GSM8K fetch.")
        except Exception as e:
            print(f"Error fetching GSM8K: {e}", file=sys.stderr)
            # Fail loudly as per constraints
            sys.exit(1)

    if args.task in ['minigrid', 'all']:
        print(f"Generating MiniGrid ground truth...")
        try:
            if args.seed is not None and args.map_id is not None:
                # Single specific generation
                generate_minigrid_paths(args.seed, args.map_id, output_path)
                print(f"Generated path for seed={args.seed}, map_id={args.map_id}")
            else:
                # Batch generation
                fetch_minigrid_ground_truth(output_path, limit=args.limit)
                print(f"Completed MiniGrid generation for {args.limit} seeds.")
        except Exception as e:
            print(f"Error generating MiniGrid paths: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Ground truth paths written to {output_path}")

if __name__ == "__main__":
    main()
