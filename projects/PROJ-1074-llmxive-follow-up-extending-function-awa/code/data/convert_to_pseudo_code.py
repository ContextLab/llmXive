import json
import sys
import argparse
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Import shared utilities from the project's common module
try:
    from utils.common import get_logger, ensure_dir, write_json
except ImportError:
    # Fallback for direct execution if path is not set up, though project structure implies utils is available
    import logging
    import os
    from pathlib import Path

    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def ensure_dir(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def write_json(path: Path, data: Any) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

def extract_steps_from_gsm8k_question(question_text: str) -> List[str]:
    """
    Extracts logical deduction steps from a GSM8K question text.
    Splits on newlines and filters for meaningful deduction lines.
    """
    lines = question_text.split('\n')
    steps = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('Question:') and not stripped.startswith('Answer:'):
            # Heuristic: lines that look like reasoning steps
            if 'Therefore' in stripped or 'So' in stripped or '=' in stripped or 'is' in stripped:
                steps.append(stripped)
    return steps

def convert_gsm8k_to_pseudo_code(steps: List[str], example_id: str) -> Dict[str, Any]:
    """
    Converts a list of deduction steps into pseudo-code blocks.
    Each step becomes a function `def step_N():` returning the derived fact.
    Returns a dictionary representing the example with pseudo-code and metadata.
    """
    pseudo_code_lines = []
    step_map = {}

    for i, step in enumerate(steps):
        func_name = f"step_{i}"
        # Escape quotes in the step text to ensure valid string representation
        safe_step = step.replace('"', '\\"').replace('\n', '\\n')
        func_def = f'def {func_name}():\n    return "{safe_step}"'
        pseudo_code_lines.append(func_def)
        step_map[func_name] = step

    return {
        "id": example_id,
        "original_steps": steps,
        "pseudo_code": "\n\n".join(pseudo_code_lines),
        "step_map": step_map
    }

def extract_dependency_graph(example: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts the dependency graph from a pseudo-code converted example.
    Identifies `step_N` calls within the step text to build edges.
    
    Returns:
        Dict with 'nodes' (list of step names) and 'edges' (list of [from, to]).
        Edges are directed: [caller, callee] meaning 'caller depends on callee'.
    """
    step_map = example.get("step_map", {})
    nodes = list(step_map.keys())
    edges = []
    
    # Regex to find step_N calls in the text
    # Matches 'step_0', 'step_1', etc.
    step_ref_pattern = re.compile(r'step_(\d+)')

    for func_name, text in step_map.items():
        # Find all references to other steps in this step's text
        matches = step_ref_pattern.findall(text)
        for ref_idx in matches:
            ref_func_name = f"step_{ref_idx}"
            if ref_func_name in step_map:
                # Edge: func_name depends on ref_func_name
                # We store as [dependent, dependency]
                edges.append([func_name, ref_func_name])
    
    return {
        "id": example["id"],
        "nodes": nodes,
        "edges": edges,
        "is_acyclic": True # Placeholder, actual cycle detection handled in validate_dependencies
    }

def main():
    parser = argparse.ArgumentParser(description="Convert GSM8K to pseudo-code and extract dependency graphs.")
    parser.add_argument("--input", type=str, required=True, help="Path to GSM8K JSONL file (raw/processed)")
    parser.add_argument("--output-steps", type=str, required=True, help="Path to output intermediate_steps.jsonl")
    parser.add_argument("--output-graphs", type=str, required=True, help="Path to output dependency_graphs.json")
    parser.add_argument("--max-examples", type=int, default=None, help="Maximum number of examples to process (for testing)")
    
    args = parser.parse_args()
    logger = get_logger("convert_to_pseudo_code")
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    intermediate_steps_path = Path(args.output_steps)
    graphs_path = Path(args.output_graphs)
    
    ensure_dir(intermediate_steps_path.parent)
    ensure_dir(graphs_path.parent)

    logger.info(f"Reading input from {input_path}")
    
    converted_examples = []
    dependency_graphs = []
    
    with open(input_path, 'r', encoding='utf-8') as f_in:
        for line_num, line in enumerate(f_in):
            if args.max_examples and line_num >= args.max_examples:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                raw_data = json.loads(line)
                # GSM8K format typically has 'question' and 'answer'
                question = raw_data.get('question', '')
                example_id = raw_data.get('id', f"unknown_{line_num}")
                
                # 1. Extract steps
                steps = extract_steps_from_gsm8k_question(question)
                if not steps:
                    logger.warning(f"No steps found for example {example_id}, skipping.")
                    continue
                
                # 2. Convert to pseudo-code
                pseudo_example = convert_gsm8k_to_pseudo_code(steps, example_id)
                converted_examples.append(pseudo_example)
                
                # 3. Extract dependency graph
                graph_data = extract_dependency_graph(pseudo_example)
                dependency_graphs.append(graph_data)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON at line {line_num}")
                continue
            except Exception as e:
                logger.error(f"Error processing example {line_num}: {e}")
                continue

    # Write intermediate steps (pseudo-code)
    logger.info(f"Writing {len(converted_examples)} examples to {intermediate_steps_path}")
    with open(intermediate_steps_path, 'w', encoding='utf-8') as f_out:
        for example in converted_examples:
            f_out.write(json.dumps(example) + '\n')
    
    # Write dependency graphs
    logger.info(f"Writing {len(dependency_graphs)} graphs to {graphs_path}")
    write_json(graphs_path, dependency_graphs)
    
    logger.info("Conversion and graph extraction complete.")

if __name__ == "__main__":
    main()