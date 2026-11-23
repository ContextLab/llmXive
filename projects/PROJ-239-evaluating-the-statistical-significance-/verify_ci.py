"""
Script to verify CI configuration file.
"""
import sys
import yaml

def main():
    """Verify .github/workflows/ci.yml exists and has correct structure."""
    ci_path = '.github/workflows/ci.yml'
    
    try:
        with open(ci_path, 'r') as f:
            workflow = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: CI configuration file not found: {ci_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML in CI configuration: {e}")
        sys.exit(1)

    # Check runs-on
    try:
        runs_on = workflow['jobs']['build']['runs-on']
        assert runs_on == 'ubuntu-latest', f"Expected 'ubuntu-latest', got '{runs_on}'"
        print(f"✓ runs-on is 'ubuntu-latest'")
    except (KeyError, AssertionError) as e:
        print(f"ERROR: Invalid runs-on configuration: {e}")
        sys.exit(1)

    # Check for cache step
    try:
        steps = workflow['jobs']['build']['steps']
        cache_step = None
        for step in steps:
            if 'actions/cache@v4' in step.get('uses', ''):
                cache_step = step
                break
        
        assert cache_step is not None, "No actions/cache@v4 step found"
        assert 'with' in cache_step, "Cache step missing 'with' key"
        assert 'path' in cache_step['with'], "Cache step missing 'path' in 'with'"
        print(f"✓ Cache step found with 'path' configuration")
    except (KeyError, AssertionError) as e:
        print(f"ERROR: Invalid cache configuration: {e}")
        sys.exit(1)

    print("✓ CI configuration is valid")
    sys.exit(0)

if __name__ == '__main__':
    main()