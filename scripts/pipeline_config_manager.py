#!/usr/bin/env python3
"""
Pipeline Configuration Manager for llmXive

Handles loading, validation, and management of YAML-based pipeline configurations
with support for dynamic dependencies, model selection, and file routing.
"""

import os
import sys
import yaml
import json
import re
import ast
import operator
import jsonschema
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    """Tracks the current state of pipeline execution"""
    variables: Dict[str, Any] = field(default_factory=dict)
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    step_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    step_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get variable value with optional default"""
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value"""
        self.variables[name] = value
    
    def is_step_completed(self, step_name: str) -> bool:
        """Check if step is completed"""
        return step_name in self.completed_steps
    
    def is_step_failed(self, step_name: str) -> bool:
        """Check if step failed"""
        return step_name in self.failed_steps


class ExpressionEvaluator:
    """Safe expression evaluator for pipeline conditions"""
    
    # Allowed operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.FloorDiv: operator.floordiv,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
    }
    
    def __init__(self, state: PipelineState):
        self.state = state
    
    def evaluate(self, expression: str) -> Any:
        """Safely evaluate an expression"""
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            return self._eval_node(tree.body)
        except Exception as e:
            logger.warning(f"Expression evaluation failed: {expression} -> {e}")
            return False
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Variable lookup
            return self.state.get_variable(node.id, False)
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, right_node in zip(node.ops, node.comparators):
                right = self._eval_node(right_node)
                op_func = self.OPERATORS.get(type(op))
                if op_func:
                    if not op_func(left, right):
                        return False
                    left = right  # For chained comparisons
                else:
                    raise ValueError(f"Unsupported comparison: {type(op)}")
            return True
        elif isinstance(node, ast.BoolOp):
            op = self.OPERATORS.get(type(node.op))
            if op:
                values = [self._eval_node(value) for value in node.values]
                result = values[0]
                for value in values[1:]:
                    result = op(result, value)
                return result
            else:
                raise ValueError(f"Unsupported boolean operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")


class ModelSelector:
    """Handles model selection based on criteria and constraints"""
    
    def __init__(self, models_config: Dict[str, Any]):
        self.models = models_config
        self.usage_history = []
    
    def select_model(self, criteria: Dict[str, Any], exclude_previous: bool = False) -> Optional[str]:
        """Select best model based on criteria"""
        candidates = []
        
        for model_name, model_info in self.models.items():
            if self._matches_criteria(model_name, model_info, criteria):
                candidates.append((model_name, model_info))
        
        if exclude_previous and self.usage_history:
            last_model = self.usage_history[-1]
            candidates = [(name, info) for name, info in candidates if name != last_model]
        
        if not candidates:
            # Try fallback
            fallback = criteria.get('fallback', '*')
            if fallback == '*':
                # Any available model
                if self.models:
                    model_name = list(self.models.keys())[0]
                    logger.warning(f"Using fallback model: {model_name}")
                    return model_name
            return None
        
        # Select best candidate (by parameter count, cost, etc.)
        selected = self._select_best_candidate(candidates, criteria)
        
        if selected:
            self.usage_history.append(selected)
            logger.info(f"Selected model: {selected}")
        
        return selected
    
    def _matches_criteria(self, model_name: str, model_info: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if model matches selection criteria"""
        # Check provider
        if 'provider' in criteria and model_info.get('provider') != criteria['provider']:
            return False
        
        # Check parameter count
        model_params = model_info.get('parameters', 0)
        if 'min_parameters' in criteria and model_params < criteria['min_parameters']:
            return False
        if 'max_parameters' in criteria and model_params > criteria['max_parameters']:
            return False
        
        # Check preferred models (with wildcards)
        preferred = criteria.get('preferred_models', [])
        if preferred and not any(self._matches_pattern(model_name, pattern) for pattern in preferred):
            return False
        
        # Check excluded models
        excluded = criteria.get('exclude_models', [])
        if any(self._matches_pattern(model_name, pattern) for pattern in excluded):
            return False
        
        # Check capabilities
        required_caps = criteria.get('capabilities', [])
        model_caps = model_info.get('capabilities', [])
        if not all(cap in model_caps for cap in required_caps):
            return False
        
        return True
    
    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches pattern (supports wildcards)"""
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f"^{regex_pattern}$", name) is not None
    
    def _select_best_candidate(self, candidates: List[Tuple[str, Dict]], criteria: Dict[str, Any]) -> Optional[str]:
        """Select the best candidate from the list"""
        if not candidates:
            return None
        
        # Sort by preference: parameter count (desc), cost (asc)
        def sort_key(candidate):
            name, info = candidate
            params = info.get('parameters', 0)
            cost = info.get('cost_per_token', float('inf'))
            return (-params, cost)  # Negative for descending order
        
        candidates.sort(key=sort_key)
        return candidates[0][0]


class FileRouter:
    """Handles file routing with glob patterns and dynamic naming"""
    
    def __init__(self, base_path: Path, state: PipelineState):
        self.base_path = base_path
        self.state = state
    
    def resolve_input_files(self, patterns: List[str]) -> List[Path]:
        """Resolve input file patterns to actual file paths"""
        files = []
        for pattern in patterns:
            resolved_pattern = self._substitute_variables(pattern)
            matched_files = list(self.base_path.glob(resolved_pattern))
            files.extend(matched_files)
        return files
    
    def resolve_output_paths(self, patterns: List[str], step_name: str) -> List[Path]:
        """Resolve output file patterns to target paths"""
        paths = []
        for pattern in patterns:
            resolved_pattern = self._substitute_variables(pattern, step_name=step_name)
            path = self.base_path / resolved_pattern
            path.parent.mkdir(parents=True, exist_ok=True)
            paths.append(path)
        return paths
    
    def _substitute_variables(self, pattern: str, **extra_vars) -> str:
        """Substitute variables in file patterns"""
        variables = {
            'timestamp': datetime.now().strftime('%Y%m%d-%H%M%S'),
            'date': datetime.now().strftime('%Y%m%d'),
            'time': datetime.now().strftime('%H%M%S'),
            **self.state.variables,
            **extra_vars
        }
        
        # Replace {variable} patterns
        for var_name, var_value in variables.items():
            pattern = pattern.replace(f'{{{var_name}}}', str(var_value))
        
        return pattern


class PipelineConfigManager:
    """Main pipeline configuration management class"""
    
    def __init__(self, config_path: Optional[Path] = None, schema_path: Optional[Path] = None):
        self.config_path = config_path or Path("pipeline_config.yaml")
        self.schema_path = schema_path or Path("pipeline_schema.json")
        self.config = None
        self.schema = None
        self.state = PipelineState()
        self.expression_evaluator = ExpressionEvaluator(self.state)
        self.model_selector = None
        self.file_router = None
        
    def load_config(self) -> Dict[str, Any]:
        """Load and validate pipeline configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Load schema for validation
            if self.schema_path.exists():
                with open(self.schema_path, 'r') as f:
                    self.schema = json.load(f)
                
                # Validate config against schema
                jsonschema.validate(self.config, self.schema)
                logger.info("Configuration validated successfully")
            
            # Initialize components
            self._initialize_components()
            
            return self.config
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise
        except jsonschema.ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration and return errors"""
        errors = []
        
        try:
            if self.schema:
                jsonschema.validate(config, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation: {e.message}")
        
        # Additional semantic validation
        errors.extend(self._validate_dependencies(config))
        errors.extend(self._validate_model_references(config))
        errors.extend(self._validate_file_patterns(config))
        
        return len(errors) == 0, errors
    
    def get_execution_order(self) -> List[str]:
        """Get step execution order using topological sort"""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        steps = self.config.get('steps', {})
        
        # Build dependency graph
        graph = {}
        in_degree = {}
        
        for step_name in steps:
            graph[step_name] = []
            in_degree[step_name] = 0
        
        for step_name, step_config in steps.items():
            for dep in step_config.get('depends_on', []):
                if dep in steps:
                    graph[dep].append(step_name)
                    in_degree[step_name] += 1
        
        # Topological sort
        queue = [step for step, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(steps):
            # Circular dependency detected
            remaining = set(steps.keys()) - set(result)
            raise ValueError(f"Circular dependency detected involving: {remaining}")
        
        return result
    
    def can_execute_step(self, step_name: str) -> Tuple[bool, str]:
        """Check if a step can be executed based on dependencies and conditions"""
        if not self.config:
            return False, "Configuration not loaded"
        
        step_config = self.config['steps'].get(step_name)
        if not step_config:
            return False, f"Step {step_name} not found"
        
        # Check dependencies
        for dep in step_config.get('depends_on', []):
            if not self.state.is_step_completed(dep):
                return False, f"Dependency {dep} not completed"
        
        # Check conditions
        for condition in step_config.get('conditions', []):
            if not self.expression_evaluator.evaluate(condition):
                return False, f"Condition not met: {condition}"
        
        return True, "Ready to execute"
    
    def apply_consequences(self, step_name: str, step_result: Dict[str, Any]) -> None:
        """Apply step consequences to pipeline state"""
        if not self.config:
            return
        
        step_config = self.config['steps'].get(step_name, {})
        
        for consequence in step_config.get('consequences', []):
            self._apply_consequence(consequence, step_result)
        
        # Mark step as completed
        self.state.completed_steps.add(step_name)
        self.state.step_outputs[step_name] = step_result
    
    def _initialize_components(self):
        """Initialize pipeline components"""
        models_config = self.config.get('models', {})
        self.model_selector = ModelSelector(models_config)
        
        base_path = Path(self.config.get('settings', {}).get('base_directory', '.'))
        self.file_router = FileRouter(base_path, self.state)
    
    def _apply_consequence(self, consequence: str, step_result: Dict[str, Any]):
        """Apply a single consequence expression"""
        try:
            # Parse assignment or operation
            if '=' in consequence:
                if '+=' in consequence:
                    var_name, expression = consequence.split('+=', 1)
                    var_name = var_name.strip()
                    current = self.state.get_variable(var_name, 0)
                    value = self.expression_evaluator.evaluate(expression.strip())
                    self.state.set_variable(var_name, current + value)
                elif '-=' in consequence:
                    var_name, expression = consequence.split('-=', 1)
                    var_name = var_name.strip()
                    current = self.state.get_variable(var_name, 0)
                    value = self.expression_evaluator.evaluate(expression.strip())
                    self.state.set_variable(var_name, current - value)
                else:
                    var_name, expression = consequence.split('=', 1)
                    var_name = var_name.strip()
                    
                    # Check if expression references step result
                    if 'review_score' in expression and 'review_score' in step_result:
                        value = step_result['review_score']
                    elif 'execution_result' in expression and 'execution_result' in step_result:
                        value = step_result['execution_result']
                    else:
                        value = self.expression_evaluator.evaluate(expression.strip())
                    
                    self.state.set_variable(var_name, value)
        except Exception as e:
            logger.warning(f"Failed to apply consequence '{consequence}': {e}")
    
    def _validate_dependencies(self, config: Dict[str, Any]) -> List[str]:
        """Validate step dependencies"""
        errors = []
        steps = config.get('steps', {})
        
        for step_name, step_config in steps.items():
            for dep in step_config.get('depends_on', []):
                if dep not in steps:
                    errors.append(f"Step {step_name} depends on non-existent step: {dep}")
        
        return errors
    
    def _validate_model_references(self, config: Dict[str, Any]) -> List[str]:
        """Validate model references in steps"""
        errors = []
        models = set(config.get('models', {}).keys())
        
        for step_name, step_config in config.get('steps', {}).items():
            model_selection = step_config.get('model_selection', {})
            preferred = model_selection.get('preferred_models', [])
            
            for model_pattern in preferred:
                if '*' not in model_pattern and model_pattern not in models:
                    errors.append(f"Step {step_name} references unknown model: {model_pattern}")
        
        return errors
    
    def _validate_file_patterns(self, config: Dict[str, Any]) -> List[str]:
        """Validate file patterns"""
        errors = []
        
        # Basic pattern validation - could be expanded
        for step_name, step_config in config.get('steps', {}).items():
            for pattern in step_config.get('inputs', []) + step_config.get('outputs', []):
                if '..' in pattern:
                    errors.append(f"Step {step_name} uses dangerous path pattern: {pattern}")
        
        return errors


def main():
    """Test the configuration manager"""
    manager = PipelineConfigManager()
    
    try:
        config = manager.load_config()
        print("✅ Configuration loaded successfully")
        
        execution_order = manager.get_execution_order()
        print(f"📋 Execution order: {execution_order}")
        
        for step in execution_order[:3]:  # Test first 3 steps
            can_execute, reason = manager.can_execute_step(step)
            print(f"🔍 {step}: {'✅' if can_execute else '❌'} {reason}")
            
            if can_execute:
                # Simulate step completion
                manager.apply_consequences(step, {'review_score': 8.5})
                print(f"✅ Completed {step}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()