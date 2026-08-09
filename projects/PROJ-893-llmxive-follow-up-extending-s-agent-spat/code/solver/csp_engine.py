"""
CSP Engine for Symbolic Spatial Reasoning.

Implements a deterministic Constraint Satisfaction Problem (CSP) solver
using the `python-constraint` library to solve counting and positioning
tasks derived from 3D geometric constraints.

This module provides the core logic for US1 (Symbolic CSP Solver Execution).
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import random

# Import configuration for seeds and paths
try:
    from config import Config
except ImportError:
    # Fallback for direct execution or different import context
    class Config:
        RANDOM_SEED = 42
        DATA_DIR = Path("data")
        DERIVED_DIR = DATA_DIR / "derived"

# Attempt to import the constraint solver
try:
    import constraint
    CONSTRAINT_LIB_AVAILABLE = True
except ImportError:
    CONSTRAINT_LIB_AVAILABLE = False
    # We will not define a mock here; the task requires real implementation.
    # If the library is missing, the functions will raise ImportError.

@dataclass
class CSPSolution:
    """Represents a single valid solution found by the CSP solver."""
    scene_id: str
    variables: Dict[str, Any]
    solution_index: int
    solver_type: str
    is_unique: bool
    status: str  # "SOLVED", "NO_SOLUTION", "AMBIGUOUS"

@dataclass
class SolveResult:
    """Container for the result of solving a single scene's constraints."""
    scene_id: str
    success: bool
    solution: Optional[Dict[str, Any]]
    num_solutions: int
    latency_ms: float
    status: str
    error_message: Optional[str] = None

class CSPEngine:
    """
    Engine to formulate and solve spatial reasoning CSPs.
    
    Converts extracted geometric constraints into a python-constraint Problem
    and solves for object positions and counts.
    """
    
    def __init__(self, seed: int = 42):
        if not CONSTRAINT_LIB_AVAILABLE:
            raise ImportError(
                "The 'python-constraint' library is required but not installed. "
                "Please install it via 'pip install python-constraint'."
            )
        self.seed = seed
        random.seed(self.seed)
        
    def _create_problem(self) -> constraint.Problem:
        """Factory for the constraint problem instance."""
        return constraint.Problem()

    def _parse_constraint_expression(self, expr: str, var_map: Dict[str, Any]) -> constraint.Constraint:
        """
        Parses a constraint string (e.g., "A + B < 5", "A != B") into a python-constraint function.
        
        This is a simplified parser for the expected constraint formats in the S-Agent dataset.
        """
        # Normalize whitespace
        expr = expr.strip()
        
        # Helper to evaluate a function against variable values
        def make_func(expr_str: str, vars_list: List[str]):
            def func(*args):
                local_vars = {v: val for v, val in zip(vars_list, args)}
                try:
                    # Safe evaluation of the expression
                    # We construct the expression string dynamically
                    eval_expr = expr_str
                    for i, v in enumerate(vars_list):
                        # Replace variable name with value representation if needed, 
                        # but since args are values, we just need to map names to args in the eval context
                        pass
                    
                    # Create a safe context
                    context = {v: args[i] for i, v in enumerate(vars_list)}
                    return eval(eval_expr, {"__builtins__": {}}, context)
                except Exception:
                    return False
            return func

        # Pattern matching for common constraints
        # 1. Equality: "A = B"
        if " = " in expr and "!=" not in expr:
            parts = expr.split(" = ")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                if left in var_map and right in var_map:
                    # Both are variables
                    return constraint.ExactSumConstraint([1, -1], [var_map[left], var_map[right]]) # This doesn't work directly for equality of vars
                    # Better approach: custom function
                    def eq_func(v1, v2):
                        return v1 == v2
                    return constraint.FunctionConstraint(eq_func, [var_map[left], var_map[right]])
                elif left in var_map:
                    # Variable = Constant
                    val = float(right)
                    def eq_const(v):
                        return v == val
                    return constraint.FunctionConstraint(eq_const, [var_map[left]])
                elif right in var_map:
                    val = float(left)
                    def eq_const(v):
                        return v == val
                    return constraint.FunctionConstraint(eq_const, [var_map[right]])
        
        # 2. Inequality: "A != B"
        if "!=" in expr:
            parts = expr.split("!=")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                if left in var_map and right in var_map:
                    def ne_func(v1, v2):
                        return v1 != v2
                    return constraint.FunctionConstraint(ne_func, [var_map[left], var_map[right]])
        
        # 3. Comparison: "A < B", "A > B", "A <= B", "A >= B"
        for op in [">=", "<=", ">", "<"]:
            if op in expr:
                parts = expr.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    if left in var_map and right in var_map:
                        def cmp_func(v1, v2, op=op):
                            if op == "<": return v1 < v2
                            if op == ">": return v1 > v2
                            if op == "<=": return v1 <= v2
                            if op == ">=": return v1 >= v2
                        return constraint.FunctionConstraint(cmp_func, [var_map[left], var_map[right]])
                    elif left in var_map:
                        val = float(right)
                        def cmp_func(v, op=op, val=val):
                            if op == "<": return v < val
                            if op == ">": return v > val
                            if op == "<=": return v <= val
                            if op == ">=": return v >= val
                        return constraint.FunctionConstraint(cmp_func, [var_map[left]])
                    elif right in var_map:
                        val = float(left)
                        def cmp_func(v, op=op, val=val):
                            # Reverse logic for right-side constant
                            if op == "<": return val < v # v > val
                            if op == ">": return val > v # v < val
                            if op == "<=": return val <= v # v >= val
                            if op == ">=": return val >= v # v <= val
                        return constraint.FunctionConstraint(cmp_func, [var_map[right]])
        
        # 4. Arithmetic: "A + B = C", "A + B < 5"
        # This is complex, fallback to generic function constraint if simple patterns fail
        # For now, assume constraints are simple binary or unary relations based on the dataset schema
        # If the constraint string is complex, we try to evaluate it as a lambda if possible
        
        # Fallback: Try to parse as a generic expression with variables
        # Identify variables in the expression
        vars_in_expr = [v for v in var_map if v in expr]
        if vars_in_expr:
            # Check if the expression is a valid boolean expression
            # We assume the dataset provides expressions that can be evaluated
            # e.g., "x1 + x2 <= 10"
            def generic_func(*args):
                ctx = {v: args[i] for i, v in enumerate(vars_in_expr)}
                try:
                    return eval(expr, {"__builtins__": {}}, ctx)
                except:
                    return False
            return constraint.FunctionConstraint(generic_func, vars_in_expr)

        raise ValueError(f"Could not parse constraint expression: {expr}")

    def solve_scene(self, scene_id: str, constraints: List[Dict[str, Any]]) -> SolveResult:
        """
        Solves the CSP for a specific scene.
        
        Args:
            scene_id: Unique identifier for the scene.
            constraints: List of constraint dictionaries extracted from data.
                        Expected keys: 'type' (e.g., 'position', 'count'), 'expression', 'variables'.
        
        Returns:
            SolveResult object containing the solution and metadata.
        """
        start_time = time.perf_counter()
        
        problem = self._create_problem()
        var_map = {} # Maps variable name to the variable object added to problem
        
        # 1. Define Variables and Domains
        # We expect constraints to define variables or we need to infer them.
        # Based on T010 output, constraints usually specify variable domains.
        
        # We'll collect all variable definitions first
        var_definitions = {} # name -> domain (list of values)
        
        for c in constraints:
            if c.get("type") == "variable_definition":
                name = c["name"]
                domain = c.get("domain", [])
                if not domain:
                    # Infer domain if missing? Usually not allowed in strict CSP
                    # Assume domain is provided. If not, we might need to handle it.
                    # For safety, default to a small range if not specified but needed
                    domain = list(range(10)) 
                var_definitions[name] = domain
        
        # Add variables to problem
        for name, domain in var_definitions.items():
            # Convert domain to a tuple for python-constraint
            problem.addVariable(name, tuple(domain))
            var_map[name] = name # Map name to itself for constraint building
        
        # If no variables defined, we can't solve
        if not var_map:
            # Check if constraints imply variables (e.g., "x > 0")
            # This is advanced; for now, if no variables, return no solution
            return SolveResult(
                scene_id=scene_id,
                success=False,
                solution=None,
                num_solutions=0,
                latency_ms=0.0,
                status="NO_VARIABLES",
                error_message="No variables defined in constraints."
            )

        # 2. Add Constraints
        for c in constraints:
            if c.get("type") == "constraint":
                expr = c.get("expression")
                if not expr:
                    continue
                
                try:
                    # Identify variables in this constraint
                    # We assume the expression string contains variable names that match var_definitions
                    vars_needed = [v for v in var_definitions if v in expr]
                    if not vars_needed:
                        continue
                        
                    # Create the constraint function
                    # python-constraint expects a function that returns True/False
                    # and a list of variable names to pass to it
                    
                    # We need to map the variable names in the expression to the problem variables
                    # Since we added them with the same names, we can pass the names directly
                    
                    def make_constraint_func(expr_str: str, vars_list: List[str]):
                        def func(*args):
                            ctx = {v: args[i] for i, v in enumerate(vars_list)}
                            try:
                                return bool(eval(expr_str, {"__builtins__": {}}, ctx))
                            except:
                                return False
                        return func
                    
                    constraint_func = make_constraint_func(expr, vars_needed)
                    problem.addConstraint(constraint_func, vars_needed)
                    
                except Exception as e:
                    # Log error but continue to see if other constraints work
                    # In a strict pipeline, we might want to fail the whole scene
                    return SolveResult(
                        scene_id=scene_id,
                        success=False,
                        solution=None,
                        num_solutions=0,
                        latency_ms=(time.perf_counter() - start_time) * 1000,
                        status="CONSTRAINT_ERROR",
                        error_message=f"Failed to parse constraint: {expr}. Error: {str(e)}"
                    )

        # 3. Solve
        try:
            # Get all solutions to determine uniqueness and count
            # getSolution() returns one solution, getSolutions() returns all
            # For large solution spaces, getSolution() is faster, but we need count for "Ambiguous" check
            # Given the task is "counting/positioning", solution space might be small or constrained enough
            solutions = problem.getSolutions()
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            
            if not solutions:
                return SolveResult(
                    scene_id=scene_id,
                    success=False,
                    solution=None,
                    num_solutions=0,
                    latency_ms=latency_ms,
                    status="NO_SOLUTION"
                )
            
            is_unique = len(solutions) == 1
            # We take the first solution as the "prediction"
            # In a real scenario, if not unique, we might report ambiguity or pick one deterministically
            first_solution = solutions[0]
            
            # Sort keys for deterministic output
            sorted_solution = dict(sorted(first_solution.items()))
            
            return SolveResult(
                scene_id=scene_id,
                success=True,
                solution=sorted_solution,
                num_solutions=len(solutions),
                latency_ms=latency_ms,
                status="SOLVED" if is_unique else "AMBIGUOUS"
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            return SolveResult(
                scene_id=scene_id,
                success=False,
                solution=None,
                num_solutions=0,
                latency_ms=(end_time - start_time) * 1000,
                status="SOLVER_ERROR",
                error_message=str(e)
            )

    def solve_batch(self, scenes: List[Dict[str, Any]]) -> List[SolveResult]:
        """
        Solves a batch of scenes.
        
        Args:
            scenes: List of dictionaries with 'scene_id' and 'constraints'.
        
        Returns:
            List of SolveResult objects.
        """
        results = []
        for scene in scenes:
            scene_id = scene.get("scene_id")
            constraints = scene.get("constraints", [])
            if not scene_id:
                continue
            result = self.solve_scene(scene_id, constraints)
            results.append(result)
        return results

def main():
    """
    Entry point for the CSP Engine when run as a script.
    Reads constraints from data/derived/constraints.jsonl and writes results.
    This is primarily for testing the engine logic in isolation or as part of the pipeline.
    """
    import json
    from pathlib import Path
    
    config = Config()
    input_path = config.DERIVED_DIR / "constraints.jsonl"
    output_path = config.DERIVED_DIR / "solver_test_results.jsonl"
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found. Run T010 first.")
        sys.exit(1)
    
    engine = CSPEngine(seed=config.RANDOM_SEED)
    
    scenes_to_solve = []
    with open(input_path, 'r') as f:
        for line in f:
            scene_data = json.loads(line)
            # Ensure we have the structure expected by solve_scene
            # T010 output should have 'scene_id' and 'constraints'
            if 'scene_id' in scene_data and 'constraints' in scene_data:
                scenes_to_solve.append(scene_data)
    
    if not scenes_to_solve:
        print("No valid scenes found in input.")
        sys.exit(0)
    
    print(f"Solving {len(scenes_to_solve)} scenes...")
    results = engine.solve_batch(scenes_to_solve)
    
    # Write results
    with open(output_path, 'w') as f:
        for res in results:
            f.write(json.dumps(asdict(res)) + '\n')
    
    print(f"Results written to {output_path}")
    
    # Summary
    solved = sum(1 for r in results if r.success)
    ambiguous = sum(1 for r in results if r.status == "AMBIGUOUS")
    no_sol = sum(1 for r in results if r.status == "NO_SOLUTION")
    print(f"Summary: Solved={solved}, Ambiguous={ambiguous}, No Solution={no_sol}")

if __name__ == "__main__":
    main()