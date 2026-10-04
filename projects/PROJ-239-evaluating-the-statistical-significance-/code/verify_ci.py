"""
Verification script for CI configuration.
Parses .github/workflows/ci.yml and asserts required fields.
"""
import sys
import yaml

def main():
    try:
        with open('.github/workflows/ci.yml', 'r') as f:
            workflow = yaml.safe_load(f)

        # Verify structure
        assert 'jobs' in workflow, "Missing 'jobs' key"
        assert 'build' in workflow['jobs'], "Missing 'build' job"
        assert 'runs-on' in workflow['jobs']['build'], "Missing 'runs-on' in build job"

        # Verify specific value
        runs_on = workflow['jobs']['build']['runs-on']
        assert runs_on == 'ubuntu-latest', f"Expected 'ubuntu-latest', got '{runs_on}'"

        print("CI configuration validated successfully.")
        sys.exit(0)

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
    except AssertionError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: .github/workflows/ci.yml not found")
        sys.exit(1)

if __name__ == '__main__':
    main()