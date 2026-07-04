import sys
import importlib.metadata

def check_dependencies():
    required = ['pandas', 'numpy', 'scipy', 'streamlit']
    missing = []
    for pkg in required:
        try:
            importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            missing.append(pkg)
    
    if missing:
        print(f"Missing dependencies: {missing}")
        return False
    return True

def main():
    if check_dependencies():
        print("All dependencies present.")
    else:
        print("Please install missing dependencies.")
