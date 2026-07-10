import ast
import random
from typing import List, Dict, Any, Optional

class MutationError(Exception):
    """Exception raised when a mutation fails."""
    pass

class VariableSwapMutator(ast.NodeTransformer):
    """
    Swaps the names of two local variables in a function.
    Only swaps variables that are actually used (assigned and read).
    """
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.variable_names = []
        self.swap_map = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Collect all local variable names (excluding arguments)
        # We need to find assignments and uses
        body_vars = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        body_vars.add(target.id)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                body_vars.add(child.target.id)
        
        # Filter out function arguments
        arg_names = {arg.arg for arg in node.args.args}
        self.variable_names = list(body_vars - arg_names)
        
        if len(self.variable_names) >= 2:
            # Pick two distinct variables to swap
            if self.seed is not None:
                random.shuffle(self.variable_names)
            else:
                random.shuffle(self.variable_names)
            
            var1, var2 = self.variable_names[0], self.variable_names[1]
            self.swap_map = {var1: var2, var2: var1}
        
        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.swap_map:
            node.id = self.swap_map[node.id]
        return node

class OperatorFlipMutator(ast.NodeTransformer):
    """
    Flips binary operators (e.g., + to -, * to /).
    """
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.op_map = {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.Div,
            ast.Div: ast.Mult,
            ast.Mod: ast.Add,  # Modulo to addition
            ast.Pow: ast.Mult,
            ast.Lt: ast.Gt,
            ast.Gt: ast.Lt,
            ast.LtE: ast.GtE,
            ast.GtE: ast.LtE,
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
            ast.And: ast.Or,
            ast.Or: ast.And,
        }

    def visit_BinOp(self, node: ast.BinOp) -> ast.BinOp:
        if type(node.op) in self.op_map:
            node.op = self.op_map[type(node.op)]()
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.UnaryOp:
        if isinstance(node.op, ast.USub):
            node.op = ast.UAdd()
        elif isinstance(node.op, ast.UAdd):
            node.op = ast.USub()
        return node

def inject_variable_swap(code: str, seed: Optional[int] = None) -> str:
    """
    Injects a variable swap mutation into the code.
    Returns the mutated code string.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise MutationError(f"Invalid syntax in input code: {e}")

    mutator = VariableSwapMutator(seed=seed)
    try:
        mutated_tree = mutator.visit(tree)
    except Exception as e:
        raise MutationError(f"Variable swap mutation failed: {e}")

    ast.fix_missing_locations(mutated_tree)
    return ast.unparse(mutated_tree)

def inject_operator_flip(code: str, seed: Optional[int] = None) -> str:
    """
    Injects an operator flip mutation into the code.
    Returns the mutated code string.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise MutationError(f"Invalid syntax in input code: {e}")

    mutator = OperatorFlipMutator(seed=seed)
    try:
        mutated_tree = mutator.visit(tree)
    except Exception as e:
        raise MutationError(f"Operator flip mutation failed: {e}")

    ast.fix_missing_locations(mutated_tree)
    return ast.unparse(mutated_tree)

def mutate_variant(
    variant: Dict[str, Any],
    mutation_type: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Applies a specific mutation to a variant.
    
    Args:
        variant: Dictionary containing 'original_id', 'code', and other metadata.
        mutation_type: Either 'variable_swap' or 'operator_flip'.
        seed: Optional seed for reproducibility.
    
    Returns:
        Dictionary with 'mutation_type', 'modified_code', 'original_id'.
    """
    original_code = variant.get('code')
    if not original_code:
        raise MutationError("Variant missing 'code' field")
    
    original_id = variant.get('original_id')
    if not original_id:
        raise MutationError("Variant missing 'original_id' field")

    if mutation_type == 'variable_swap':
        modified_code = inject_variable_swap(original_code, seed=seed)
    elif mutation_type == 'operator_flip':
        modified_code = inject_operator_flip(original_code, seed=seed)
    else:
        raise ValueError(f"Unknown mutation type: {mutation_type}")
    
    # Verify the mutated code is still valid Python
    try:
        ast.parse(modified_code)
    except SyntaxError as e:
        # If mutation broke syntax, return original with a note or skip
        # For this implementation, we'll raise an error to be caught by generator
        raise MutationError(f"Mutated code has syntax error: {e}")

    return {
        'mutation_type': mutation_type,
        'modified_code': modified_code,
        'original_id': original_id
    }

def main():
    """
    Simple test of the mutator.
    """
    test_code = """
def add_numbers(a, b):
    x = a + b
    y = a * b
    return x + y
"""
    print("Original:")
    print(test_code)
    
    print("\nVariable Swap Mutation:")
    try:
        swapped = inject_variable_swap(test_code, seed=42)
        print(swapped)
    except MutationError as e:
        print(f"Error: {e}")
    
    print("\nOperator Flip Mutation:")
    try:
        flipped = inject_operator_flip(test_code, seed=42)
        print(flipped)
    except MutationError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()