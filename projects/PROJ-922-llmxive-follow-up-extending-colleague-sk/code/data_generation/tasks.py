import json
import random
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Task templates for different domains
TASK_TEMPLATES = {
    "coding": [
        "Write a Python function that {action} for {input_type}.",
        "Create a class that implements {pattern} with {method_count} methods.",
        "Debug the following code snippet: {snippet}",
        "Optimize the algorithm for {complexity} time complexity."
    ],
    "math": [
        "Prove that {theorem_statement} using {proof_method}.",
        "Solve the equation {equation} for {variable}.",
        "Calculate the {operation} of {expression}.",
        "Derive the formula for {concept}."
    ],
    "logic": [
        "Determine if the following argument is valid: {premises} therefore {conclusion}.",
        "Identify the logical fallacy in: {statement}.",
        "Construct a truth table for {expression}.",
        "Prove the equivalence of {formula1} and {formula2}."
    ],
    "creative": [
        "Write a short story about {character} who {action} in {setting}.",
        "Compose a poem using the metaphor {metaphor}.",
        "Describe the scene where {event} happens using sensory details.",
        "Create a dialogue between {character1} and {character2} about {topic}."
    ],
    "factual": [
        "Summarize the findings of {study_topic} from {source}.",
        "Explain the concept of {concept} with examples.",
        "Compare and contrast {entity1} and {entity2}.",
        "List the key events in the history of {topic}."
    ]
}

# Sample data for task generation
SAMPLE_DATA = {
    "coding": {
        "actions": ["sort a list", "reverse a string", "find duplicates", "calculate factorial"],
        "input_types": ["integers", "strings", "lists", "dictionaries"],
        "patterns": ["Singleton", "Factory", "Observer", "Strategy"],
        "method_counts": [3, 5, 7],
        "complexities": ["O(n log n)", "O(n)", "O(1)"]
    },
    "math": {
        "theorem_statements": ["a^2 + b^2 = c^2", "e^(i*pi) + 1 = 0", "sqrt(2) is irrational"],
        "proof_methods": ["induction", "contradiction", "direct proof", "construction"],
        "equations": ["2x + 5 = 15", "x^2 - 4x + 4 = 0", "sin(x) = 0.5"],
        "variables": ["x", "y", "z"],
        "operations": ["derivative", "integral", "limit", "summation"],
        "expressions": ["x^2 + 3x + 2", "sin(x) * cos(x)", "e^(2x)"]
    },
    "logic": {
        "premises": ["All humans are mortal", "Socrates is human", "If P then Q"],
        "conclusions": ["Socrates is mortal", "Q is true", "P is false"],
        "statements": ["This statement is false", "I always lie", "All birds can fly"],
        "expressions": ["P AND Q", "P OR NOT Q", "IF P THEN Q"],
        "formulas": ["(P AND Q) IMPLIES R", "NOT (P OR Q)"]
    },
    "creative": {
        "characters": ["a lost traveler", "a wise old wizard", "a curious child"],
        "actions": ["discovers a hidden treasure", "meets a mysterious stranger", "solves an ancient riddle"],
        "settings": ["an enchanted forest", "a forgotten city", "a distant planet"],
        "metaphors": ["time is a thief", "love is a battlefield", "hope is a bird"],
        "events": ["a sudden storm", "a miraculous rescue", "a shocking revelation"],
        "topics": ["friendship", "betrayal", "redemption"]
    },
    "factual": {
        "study_topics": ["climate change", "artificial intelligence", "quantum computing"],
        "sources": ["Nature", "Science", "The Lancet", "arXiv"],
        "concepts": ["machine learning", "blockchain", "neural networks"],
        "entity1": ["Python", "Java", "C++"],
        "entity2": ["TensorFlow", "PyTorch", "Keras"],
        "topics": ["World War II", "Renaissance", "Industrial Revolution"]
    }
}

def generate_coding_task() -> Dict[str, Any]:
    """Generate a coding task."""
    template = random.choice(TASK_TEMPLATES["coding"])
    data = SAMPLE_DATA["coding"]
    
    if "{action}" in template:
        template = template.replace("{action}", random.choice(data["actions"]))
    if "{input_type}" in template:
        template = template.replace("{input_type}", random.choice(data["input_types"]))
    if "{pattern}" in template:
        template = template.replace("{pattern}", random.choice(data["patterns"]))
    if "{method_count}" in template:
        template = template.replace("{method_count}", str(random.choice(data["method_counts"])))
    if "{complexity}" in template:
        template = template.replace("{complexity}", random.choice(data["complexities"]))
    
    return {
        "type": "coding",
        "text": template,
        "validation_type": "ast"
    }

def generate_math_task() -> Dict[str, Any]:
    """Generate a math task."""
    template = random.choice(TASK_TEMPLATES["math"])
    data = SAMPLE_DATA["math"]
    
    if "{theorem_statement}" in template:
        template = template.replace("{theorem_statement}", random.choice(data["theorem_statements"]))
    if "{proof_method}" in template:
        template = template.replace("{proof_method}", random.choice(data["proof_methods"]))
    if "{equation}" in template:
        template = template.replace("{equation}", random.choice(data["equations"]))
    if "{variable}" in template:
        template = template.replace("{variable}", random.choice(data["variables"]))
    if "{operation}" in template:
        template = template.replace("{operation}", random.choice(data["operations"]))
    if "{expression}" in template:
        template = template.replace("{expression}", random.choice(data["expressions"]))
    
    return {
        "type": "math",
        "text": template,
        "validation_type": "sympy"
    }

def generate_logic_task() -> Dict[str, Any]:
    """Generate a logic task."""
    template = random.choice(TASK_TEMPLATES["logic"])
    data = SAMPLE_DATA["logic"]
    
    if "{premises}" in template:
        template = template.replace("{premises}", random.choice(data["premises"]))
    if "{conclusion}" in template:
        template = template.replace("{conclusion}", random.choice(data["conclusions"]))
    if "{statement}" in template:
        template = template.replace("{statement}", random.choice(data["statements"]))
    if "{expression}" in template:
        template = template.replace("{expression}", random.choice(data["expressions"]))
    if "{formula1}" in template:
        template = template.replace("{formula1}", random.choice(data["formulas"]))
    if "{formula2}" in template:
        template = template.replace("{formula2}", random.choice(data["formulas"]))
    
    return {
        "type": "logic",
        "text": template,
        "validation_type": "z3"
    }

def generate_creative_task() -> Dict[str, Any]:
    """Generate a creative task."""
    template = random.choice(TASK_TEMPLATES["creative"])
    data = SAMPLE_DATA["creative"]
    
    if "{character}" in template:
        template = template.replace("{character}", random.choice(data["characters"]))
    if "{action}" in template:
        template = template.replace("{action}", random.choice(data["actions"]))
    if "{setting}" in template:
        template = template.replace("{setting}", random.choice(data["settings"]))
    if "{metaphor}" in template:
        template = template.replace("{metaphor}", random.choice(data["metaphors"]))
    if "{character1}" in template:
        template = template.replace("{character1}", random.choice(data["characters"]))
    if "{character2}" in template:
        template = template.replace("{character2}", random.choice(data["characters"]))
    if "{event}" in template:
        template = template.replace("{event}", random.choice(data["events"]))
    if "{topic}" in template:
        template = template.replace("{topic}", random.choice(data["topics"]))
    
    return {
        "type": "creative",
        "text": template,
        "validation_type": "regex"
    }

def generate_factual_task() -> Dict[str, Any]:
    """Generate a factual task."""
    template = random.choice(TASK_TEMPLATES["factual"])
    data = SAMPLE_DATA["factual"]
    
    if "{study_topic}" in template:
        template = template.replace("{study_topic}", random.choice(data["study_topics"]))
    if "{source}" in template:
        template = template.replace("{source}", random.choice(data["sources"]))
    if "{concept}" in template:
        template = template.replace("{concept}", random.choice(data["concepts"]))
    if "{entity1}" in template:
        template = template.replace("{entity1}", random.choice(data["entity1"]))
    if "{entity2}" in template:
        template = template.replace("{entity2}", random.choice(data["entity2"]))
    if "{topic}" in template:
        template = template.replace("{topic}", random.choice(data["topics"]))
    
    return {
        "type": "factual",
        "text": template,
        "validation_type": "regex"
    }

GENERATORS = {
    "coding": generate_coding_task,
    "math": generate_math_task,
    "logic": generate_logic_task,
    "creative": generate_creative_task,
    "factual": generate_factual_task
}

def generate_tasks(count: int = 200, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate stratified tasks across all domains.
    
    Args:
        count: Total number of tasks to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of task dictionaries.
    """
    set_global_seed(seed)
    tasks = []
    tasks_per_domain = count // len(GENERATORS)
    
    task_id = 0
    for domain, generator in GENERATORS.items():
        for i in range(tasks_per_domain):
            task_id += 1
            task = generator()
            task["id"] = f"task_{task_id:03d}"
            tasks.append(task)
    
    # If count is not evenly divisible, add remaining tasks randomly
    remaining = count - len(tasks)
    if remaining > 0:
        domains_list = list(GENERATORS.keys())
        for i in range(remaining):
            domain = random.choice(domains_list)
            task_id += 1
            task = GENERATORS[domain]()
            task["id"] = f"task_{task_id:03d}"
            tasks.append(task)
    
    return tasks

def validate_tasks(tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validate tasks based on their type.
    
    Args:
        tasks: List of task dictionaries.
        
    Returns:
        Tuple of (valid_tasks, error_messages).
    """
    valid_tasks = []
    errors = []
    
    for task in tasks:
        try:
            # Basic validation: check required fields
            if "id" not in task or "type" not in task or "text" not in task:
                errors.append(f"Task missing required fields: {task.get('id', 'unknown')}")
                continue
            
            # Type-specific validation
            task_type = task["type"]
            if task_type == "coding":
                # Check for Python syntax
                try:
                    ast.parse(task["text"])
                except SyntaxError:
                    # This is expected for task descriptions, not code
                    pass
            elif task_type == "math":
                # Check for mathematical expressions
                if not re.search(r'[0-9+\-*/^().xysqrt]', task["text"]):
                    errors.append(f"Math task lacks mathematical content: {task['id']}")
                    continue
            elif task_type == "logic":
                # Check for logical operators
                if not re.search(r'(AND|OR|NOT|IF|THEN|IMPLIES|ALL|SOME)', task["text"]):
                    errors.append(f"Logic task lacks logical operators: {task['id']}")
                    continue
            
            valid_tasks.append(task)
        except Exception as e:
            errors.append(f"Error validating task {task.get('id', 'unknown')}: {str(e)}")
    
    return valid_tasks, errors

def save_tasks(tasks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save tasks to a JSONL file.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to save the file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(tasks)} tasks to {output_path}")

def load_tasks(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSONL file.
    
    Args:
        input_path: Path to the file.
        
    Returns:
        List of task dictionaries.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {input_path}")
    
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks

def main():
    """Main entry point for task generation."""
    set_global_seed(42)
    
    output_path = get_data_dir() / "interim" / "tasks.jsonl"
    tasks = generate_tasks(count=200)
    valid_tasks, errors = validate_tasks(tasks)
    
    if errors:
        logger.warning(f"Validation errors: {len(errors)}")
        for error in errors[:5]:
            logger.warning(error)
    
    save_tasks(valid_tasks, output_path)
    logger.info(f"Generated and saved {len(valid_tasks)} tasks")

if __name__ == "__main__":
    main()
