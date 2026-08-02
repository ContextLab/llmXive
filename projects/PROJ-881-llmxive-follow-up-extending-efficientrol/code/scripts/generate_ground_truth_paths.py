import json
import os
import sys
import argparse
from pathlib import Path
from itertools import islice
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import minigrid, fail loudly if not available
try:
    import minigrid
    from minigrid.core.grid import Grid
    from minigrid.core.world_object import Goal, Lava, Wall
    from minigrid.minigrid_env import MiniGridEnv
    from collections import deque
except ImportError as e:
    logger.error("MiniGrid is required but not installed. Please install it with: pip install minigrid")
    sys.exit(1)


def generate_minigrid_paths(seed: int, map_id: str) -> List[str]:
    """
    Generate all valid shortest paths for a MiniGrid environment.
    
    Args:
        seed: Random seed for environment initialization
        map_id: Map identifier to configure environment
        
    Returns:
        List of action sequences (paths) from start to goal
    """
    try:
        # Create environment with specified seed and map
        env = MiniGridEnv(
            grid_size=8,  # Default size, can be adjusted
            seed=seed,
            max_steps=128
        )
        
        # Reset environment to get initial state
        obs, info = env.reset(seed=seed)
        
        # Get start and goal positions
        start_pos = env.agent_pos
        goal_pos = None
        
        # Find goal position in the grid
        for y in range(env.grid.height):
            for x in range(env.grid.width):
                obj = env.grid.get(x, y)
                if obj and obj.type == 'goal':
                    goal_pos = (x, y)
                    break
            if goal_pos:
                break
        
        if not goal_pos:
            logger.error(f"No goal found in environment with seed={seed}, map_id={map_id}")
            return []
        
        # BFS to find all shortest paths
        all_paths = []
        queue = deque([(start_pos, [])])  # (position, path)
        visited = {start_pos: 0}  # position -> distance
        shortest_distance = None
        
        while queue:
            pos, path = queue.popleft()
            
            # If we've found a shortest path and current path is longer, stop
            if shortest_distance is not None and len(path) > shortest_distance:
                continue
            
            # Check if we reached the goal
            if pos == goal_pos:
                if shortest_distance is None:
                    shortest_distance = len(path)
                all_paths.append(path)
                continue
            
            # Explore neighbors
            x, y = pos
            directions = [
                ((0, -1), 0),  # Up
                ((1, 0), 1),   # Right
                ((0, 1), 2),   # Down
                ((-1, 0), 3)   # Left
            ]
            
            for (dx, dy), action in directions:
                new_x, new_y = x + dx, y + dy
                new_pos = (new_x, new_y)
                
                # Check bounds
                if not (0 <= new_x < env.grid.width and 0 <= new_y < env.grid.height):
                    continue
                
                # Check if cell is walkable
                obj = env.grid.get(new_x, new_y)
                if obj and obj.type in ['wall', 'lava']:
                    continue
                
                # Check if we've visited this cell with a shorter or equal path
                if new_pos in visited and visited[new_pos] <= len(path) + 1:
                    continue
                
                visited[new_pos] = len(path) + 1
                new_path = path + [action]
                queue.append((new_pos, new_path))
        
        # Convert action indices to action names
        action_names = ['move_forward', 'turn_right', 'turn_left', 'pickup', 'drop', 'toggle']
        path_strings = []
        for path in all_paths:
            path_str = ','.join([action_names[a] if a < len(action_names) else f'action_{a}' for a in path])
            path_strings.append(path_str)
        
        logger.info(f"Generated {len(path_strings)} valid shortest paths for seed={seed}, map_id={map_id}")
        return path_strings
        
    except Exception as e:
        logger.error(f"Error generating MiniGrid paths: {e}")
        raise


def fetch_gsm8k_ground_truth() -> List[Dict[str, Any]]:
    """
    Fetch ground truth solutions for GSM8K dataset.
    
    Returns:
        List of dictionaries with prompt_id and ground truth solution
    """
    try:
        from datasets import load_dataset
        
        logger.info("Loading GSM8K dataset...")
        dataset = load_dataset("gsm8k", "main", split="train", streaming=True)
        
        # Take first 500 examples as per FR-001
        ground_truths = []
        for idx, example in enumerate(islice(dataset, 500)):
            ground_truths.append({
                "prompt_id": f"gsm8k_{idx:04d}",
                "task_type": "gsm8k",
                "valid_paths": [example['answer']],  # GSM8K has single solution
                "seed": 42,  # Default seed for GSM8K
                "map_id": "gsm8k_default"
            })
        
        logger.info(f"Fetched {len(ground_truths)} GSM8K ground truths")
        return ground_truths
        
    except Exception as e:
        logger.error(f"Error fetching GSM8K ground truth: {e}")
        raise


def fetch_minigrid_ground_truth(seeds: List[int], map_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch ground truth paths for MiniGrid environments.
    
    Args:
        seeds: List of random seeds
        map_ids: List of map identifiers
        
    Returns:
        List of dictionaries with prompt_id, valid_paths, seed, and map_id
    """
    ground_truths = []
    
    for idx, (seed, map_id) in enumerate(zip(seeds, map_ids)):
        try:
            paths = generate_minigrid_paths(seed, map_id)
            ground_truths.append({
                "prompt_id": f"minigrid_{idx:04d}",
                "task_type": "minigrid",
                "valid_paths": paths,
                "seed": seed,
                "map_id": map_id
            })
            logger.info(f"Processed MiniGrid {idx}: seed={seed}, map_id={map_id}, paths={len(paths)}")
        except Exception as e:
            logger.error(f"Error processing MiniGrid {idx}: {e}")
            # Continue with other seeds/maps
            continue
    
    return ground_truths


def main():
    """
    Main function to generate ground truth paths and write to JSONL file.
    """
    parser = argparse.ArgumentParser(description='Generate ground truth paths for GSM8K and MiniGrid')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for MiniGrid')
    parser.add_argument('--map-id', type=str, default='default', help='Map ID for MiniGrid')
    parser.add_argument('--output', type=str, default='data/ground_truth_paths.jsonl', 
                      help='Output file path')
    parser.add_argument('--task-type', type=str, choices=['gsm8k', 'minigrid', 'both'], 
                      default='both', help='Task type to generate')
    parser.add_argument('--minigrid-seeds', type=str, nargs='+', default=[42, 123, 456],
                      help='Multiple seeds for MiniGrid')
    parser.add_argument('--minigrid-map-ids', type=str, nargs='+', default=['default', 'grid8x8', 'grid16x16'],
                      help='Multiple map IDs for MiniGrid')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    ground_truths = []
    
    # Fetch GSM8K ground truth
    if args.task_type in ['gsm8k', 'both']:
        try:
            gsm8k_gt = fetch_gsm8k_ground_truth()
            ground_truths.extend(gsm8k_gt)
        except Exception as e:
            logger.error(f"Failed to fetch GSM8K ground truth: {e}")
            if args.task_type == 'gsm8k':
                raise
    
    # Fetch MiniGrid ground truth
    if args.task_type in ['minigrid', 'both']:
        try:
            minigrid_seeds = [int(s) for s in args.minigrid_seeds]
            minigrid_map_ids = args.minigrid_map_ids
            
            # Ensure we have matching lengths
            min_len = min(len(minigrid_seeds), len(minigrid_map_ids))
            minigrid_seeds = minigrid_seeds[:min_len]
            minigrid_map_ids = minigrid_map_ids[:min_len]
            
            minigrid_gt = fetch_minigrid_ground_truth(minigrid_seeds, minigrid_map_ids)
            ground_truths.extend(minigrid_gt)
        except Exception as e:
            logger.error(f"Failed to fetch MiniGrid ground truth: {e}")
            if args.task_type == 'minigrid':
                raise
    
    # Write to JSONL file
    with open(output_path, 'w') as f:
        for gt in ground_truths:
            f.write(json.dumps(gt) + '\n')
    
    logger.info(f"Wrote {len(ground_truths)} ground truth entries to {output_path}")
    print(f"Generated {len(ground_truths)} ground truth entries")
    print(f"Output file: {output_path}")


if __name__ == '__main__':
    main()