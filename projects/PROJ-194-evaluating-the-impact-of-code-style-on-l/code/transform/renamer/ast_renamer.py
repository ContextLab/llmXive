"""
AST Renamer implementation.
Replaces identifiers with deterministic generic tokens (e.g., var1, func2).
Ensures reproducibility by logging the mapping and its hash.
"""
import ast
from typing import Dict, List, Any, Optional
import hashlib
import sys

class GenericRenamer(ast.NodeTransformer):
    def __init__(self):
        self.func_counter = 0
        self.var_counter = 0
        self.arg_counter = 0
        self.mapping: Dict[str, str] = {}  # Original name -> Generic name
        self.builtins = {
            'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda',
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
            'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
            'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
            'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
            'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
            'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
            'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
            'tuple', 'type', 'vars', 'zip', '__import__', 'ArithmeticError',
            'AssertionError', 'AttributeError', 'BaseException', 'BlockingIOError',
            'BrokenPipeError', 'BufferError', 'BytesWarning', 'ChildProcessError',
            'ConnectionAbortedError', 'ConnectionError', 'ConnectionRefusedError',
            'ConnectionResetError', 'DeprecationWarning', 'EOFError', 'Ellipsis',
            'EnvironmentError', 'Exception', 'FileExistsError', 'FileNotFoundError',
            'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
            'ImportError', 'ImportWarning', 'IndentationError', 'IndexError',
            'InterruptedError', 'IsADirectoryError', 'KeyError', 'KeyboardInterrupt',
            'LookupError', 'MemoryError', 'ModuleNotFoundError', 'NameError',
            'NotADirectoryError', 'NotImplemented', 'NotImplementedError', 'OSError',
            'OverflowError', 'PendingDeprecationWarning', 'PermissionError',
            'ProcessLookupError', 'RecursionError', 'ReferenceError', 'ResourceWarning',
            'RuntimeError', 'RuntimeWarning', 'StopAsyncIteration', 'StopIteration',
            'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError',
            'TimeoutError', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError',
            'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',
            'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError'
        }

    def _get_generic_name(self, kind: str) -> str:
        if kind == 'func':
            name = f"func{self.func_counter}"
            self.func_counter += 1
        elif kind == 'var':
            name = f"var{self.var_counter}"
            self.var_counter += 1
        elif kind == 'arg':
            name = f"arg{self.arg_counter}"
            self.arg_counter += 1
        else:
            name = f"var{self.var_counter}"
            self.var_counter += 1
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Rename the function itself
        if node.name not in self.mapping:
            self.mapping[node.name] = self._get_generic_name('func')
        node.name = self.mapping[node.name]

        # Rename arguments
        for arg in node.args.args:
            if arg.arg not in self.mapping:
                self.mapping[arg.arg] = self._get_generic_name('arg')
            arg.arg = self.mapping[arg.arg]

        # Visit body
        self.generic_visit(node)
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id not in self.mapping:
                    self.mapping[target.id] = self._get_generic_name('var')
                target.id = self.mapping[target.id]
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        # Only rename if it's a variable usage, not a keyword or built-in
        if node.id not in self.mapping:
            if node.id not in self.builtins:
                self.mapping[node.id] = self._get_generic_name('var')
        node.id = self.mapping[node.id]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if node.name not in self.mapping:
            self.mapping[node.name] = self._get_generic_name('func')  # Treat class like func for naming
        node.name = self.mapping[node.name]
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        if isinstance(node.target, ast.Name):
            if node.target.id not in self.mapping:
                self.mapping[node.target.id] = self._get_generic_name('var')
            node.target.id = self.mapping[node.target.id]
        self.generic_visit(node)
        return node

    def visit_For(self, node: ast.For) -> ast.For:
        if isinstance(node.target, ast.Name):
            if node.target.id not in self.mapping:
                self.mapping[node.target.id] = self._get_generic_name('var')
            node.target.id = self.mapping[node.target.id]
        self.generic_visit(node)
        return node

    def visit_With(self, node: ast.With) -> ast.With:
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                if item.optional_vars.id not in self.mapping:
                    self.mapping[item.optional_vars.id] = self._get_generic_name('var')
                item.optional_vars.id = self.mapping[item.optional_vars.id]
        self.generic_visit(node)
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.ExceptHandler:
        if node.name:
            if node.name not in self.mapping:
                self.mapping[node.name] = self._get_generic_name('var')
            node.name = self.mapping[node.name]
        self.generic_visit(node)
        return node

    def get_mapping(self) -> Dict[str, str]:
        """Return the mapping of original names to generic names."""
        return self.mapping

def apply_generic_naming(code: str) -> str:
    """
    Parse code via AST and replace identifiers with deterministic generic tokens.
    
    Args:
        code: Python code string.
    
    Returns:
        Code string with generic identifiers.
    
    Raises:
        SyntaxError: If the input code is not valid Python.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax in input: {e}")

    renamer = GenericRenamer()
    new_tree = renamer.visit(tree)
    
    # Convert back to code
    # ast.unparse is available in Python 3.9+
    try:
        return ast.unparse(new_tree)
    except AttributeError:
        raise RuntimeError("ast.unparse is not available. Python 3.9+ is required.")

def main():
    """Test the renamer."""
    sample = """
    def calculate_sum(a, b):
        result = a + b
        return result
    
    class MyClass:
        def __init__(self, value):
            self.value = value
    
    obj = MyClass(10)
    total = obj.value + 5
    print(total)
    """
    try:
        result = apply_generic_naming(sample)
        print("Original:")
        print(sample)
        print("\nTransformed:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()