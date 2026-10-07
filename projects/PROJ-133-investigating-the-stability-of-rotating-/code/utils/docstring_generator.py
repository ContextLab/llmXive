import os
import inspect
import logging

def generate_docstrings(module_path: str) -> None:
    """
    Generates docstrings for all public functions and classes in a module.

    Args:
        module_path: The path to the module.
    """
    try:
        module = __import__(module_path)
    except ImportError as e:
        logging.error(f"Failed to import module {module_path}: {e}")
        return

    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):  # Skip private members
            continue

        if inspect.isfunction(obj) or inspect.isclass(obj):
            if obj.__doc__ is None:
                docstring = f"This function/class is not yet documented.  Add a docstring to explain its purpose and usage."
                setattr(obj, "__doc__", docstring)
                logging.warning(f"Added docstring to {name} in {module_path}")

def main():
    """
    Main function to generate docstrings for all modules in the current project.
    """
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    # Iterate through all .py files in the code directory
    for root, _, files in os.walk("code"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                module_path = os.path.splitext(file)[0]
                full_module_path = os.path.join(root, module_path)
                full_module_path = full_module_path.replace("code/", "")
                full_module_path = full_module_path.replace(".py", "")
                full_module_path = full_module_path.replace("/", ".")

                generate_docstrings(full_module_path)
                logging.info(f"Generated docstrings for module: {full_module_path}")

    logging.info("Docstring generation completed.")
