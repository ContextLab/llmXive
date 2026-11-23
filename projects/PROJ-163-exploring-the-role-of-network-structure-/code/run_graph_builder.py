"""
Helper script to invoke the graph builder in a way that matches the
project's quickstart command. It simply forwards any arguments to
``code.graph_builder.main``. This file exists so that the execution
request can be expressed without modifying the existing quickstart
documentation.
"""
import sys
from pathlib import Path

# Ensure the project root is on the Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import and execute the main function from the module
from code.graph_builder import main as graph_builder_main

if __name__ == "__main__":
    # Pass through command‑line arguments (excluding the script name)
    graph_builder_main()