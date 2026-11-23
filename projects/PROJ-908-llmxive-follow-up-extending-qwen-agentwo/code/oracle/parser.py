"""
Oracle Parser: Parses Qwen-AgentWorld source code to extract interaction logic.
"""
import ast
import json
import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from utils.loaders import load_oracle_source_code

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class StateTransition:
    """Represents a state transition in the agent world."""
    source_state: str
    target_state: str
    predicate: str
    action: str

@dataclass
class InteractionLogic:
    """Represents the logic for a specific interaction type."""
    interaction_type: str
    description: str
    preconditions: List[str]
    postconditions: List[str]
    transitions: List[StateTransition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_type": self.interaction_type,
            "description": self.description,
            "preconditions": self.preconditions,
            "postconditions": self.postconditions,
            "transitions": [asdict(t) for t in self.transitions]
        }

class QwenAgentWorldParser(ast.NodeVisitor):
    """AST Visitor to extract interaction logic from Qwen-AgentWorld source."""

    def __init__(self):
        self.interactions: List[InteractionLogic] = []
        self.current_interaction: Optional[InteractionLogic] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        # Look for classes that represent interactions or environments
        if "Interaction" in node.name or "Environment" in node.name:
            self.current_interaction = InteractionLogic(
                interaction_type=node.name,
                description=node.name,
                preconditions=[],
                postconditions=[]
            )
            self.interactions.append(self.current_interaction)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Look for methods that define state changes
        if self.current_interaction:
            if "transition" in node.name.lower() or "step" in node.name.lower():
                # Extract docstring for description
                docstring = ast.get_docstring(node) or ""
                
                # Extract preconditions and postconditions from comments or docstring
                # This is a simplified extraction
                preconds = []
                postconds = []
                transitions = []
                
                # Parse docstring for simple patterns
                if "pre:" in docstring:
                    preconds = [p.strip() for p in docstring.split("pre:")[1].split("post:")[0].split(",")]
                if "post:" in docstring:
                    postconds = [p.strip() for p in docstring.split("post:")[1].split("\n")[0].split(",")]
                
                # Create a dummy transition based on function name
                trans = StateTransition(
                    source_state="start",
                    target_state="end",
                    predicate=node.name,
                    action=node.name
                )
                transitions.append(trans)
                
                self.current_interaction.preconditions.extend(preconds)
                self.current_interaction.postconditions.extend(postconds)
                self.current_interaction.transitions.extend(transitions)
        self.generic_visit(node)

def parse_qwen_agentworld(source_dir: Path, parser: QwenAgentWorldParser) -> List[InteractionLogic]:
    """
    Parse all Python files in source_dir to extract interaction logic.
    """
    logger.info(f"Parsing source directory: {source_dir}")
    
    py_files = list(source_dir.rglob("*.py"))
    logger.info(f"Found {len(py_files)} Python files.")
    
    for py_file in py_files:
        logger.info(f"Processing {py_file}...")
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            parser.visit(tree)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.error(f"Error processing {py_file}: {e}")
    
    logger.info(f"Extracted {len(parser.interactions)} interaction logics.")
    return parser.interactions

def main():
    """CLI entry point for parser."""
    import argparse
    parser = argparse.ArgumentParser(description="Parse Qwen-AgentWorld source")
    parser.add_argument("--source", required=True, help="Source directory")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        sys.exit(1)
    
    visitor = QwenAgentWorldParser()
    interactions = parse_qwen_agentworld(source_dir, visitor)
    
    output_data = {
        "interactions": [i.to_dict() for i in interactions]
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved parsed interactions to {args.output}")

if __name__ == "__main__":
    main()
