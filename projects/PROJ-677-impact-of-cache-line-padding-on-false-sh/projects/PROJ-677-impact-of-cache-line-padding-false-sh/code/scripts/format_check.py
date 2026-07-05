import subprocess
import sys
import os

def run_command(cmd):
    """Run a shell command and return success status."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Run basic linting and formatting checks."""
    print("Running format checks...")
    
    # Check for clang-format
    if run_command('which clang-format'):
        print("Running clang-format check on C++ files...")
        # Check if files are formatted (dry run)
        cpp_files = [f for f in os.listdir('code/benchmark') if f.endswith('.cpp') or f.endswith('.hpp')]
        if cpp_files:
            cmd = f'clang-format --dry-run --Werror code/benchmark/{cpp_files[0]}'
            if not run_command(cmd):
                print("ERROR: C++ files are not formatted correctly.")
                return 1
    else:
        print("Warning: clang-format not found.")

    # Check for black/flake8
    if run_command('which black') and run_command('which flake8'):
        print("Running Python linting...")
        if not run_command('black --check code/'):
            print("ERROR: Python files are not formatted correctly by black.")
            return 1
        if not run_command('flake8 code/'):
            print("ERROR: Python files have linting errors.")
            return 1
    else:
        print("Warning: black or flake8 not found.")

    print("Format checks passed.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
