#!/usr/bin/env python3
"""
Test real package installation and usage
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


def test_package_installation():
    """Test installing and using a real package"""
    
    print("🧪 Package Installation Test")
    print("=" * 40)
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_pkg_"))
    print(f"📁 Test directory: {temp_dir}")
    
    try:
        # Create code execution manager
        manager = CodeExecutionManager(temp_dir)
        
        # Create project structure
        project_path = temp_dir / "package_test_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        
        # Create requirements.txt with a simple package
        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("requests>=2.25.0\n")
        print(f"📝 Created requirements.txt with requests package")
        
        # Create test script that uses the package
        test_script = code_dir / "main.py"
        test_script.write_text("""import requests
import json

print("Testing package installation...")
print(f"Requests version: {requests.__version__}")

# Test a simple HTTP request (to a reliable endpoint)
try:
    response = requests.get("https://httpbin.org/json", timeout=10)
    print(f"HTTP request successful: {response.status_code}")
    
    data = response.json()
    print(f"Response data keys: {list(data.keys())}")
    
    # Save result
    result = {
        "package_test": "success",
        "requests_version": requests.__version__,
        "http_status": response.status_code,
        "response_keys": list(data.keys())
    }
    
    with open("package_test_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("Package test completed successfully!")
    
except Exception as e:
    print(f"Error during test: {e}")
    # Still save a result showing the package was imported
    result = {
        "package_test": "partial_success",
        "requests_version": requests.__version__,
        "error": str(e)
    }
    
    with open("package_test_result.json", "w") as f:
        json.dump(result, f, indent=2)
""")
        
        print(f"📝 Created test script using requests package")
        
        # Execute the code
        print("🚀 Executing code with package installation...")
        print("⏳ This may take a while for package installation...")
        
        result = manager.execute_code(project_path, test_script, timeout=180)  # 3 minutes
        
        print("📊 RESULTS:")
        print(f"  Success: {result['success']}")
        print(f"  Exit code: {result['exit_code']}")
        print(f"  Runtime: {result['runtime_seconds']:.2f}s")
        
        if result['output']:
            print(f"  Output:")
            for line in result['output'].split('\n'):
                if line.strip():
                    print(f"    {line}")
        
        if result['error']:
            print(f"  Error: {result['error']}")
        
        # Check if result file was created
        result_file = project_path / "package_test_result.json"
        if result_file.exists():
            with open(result_file) as f:
                test_result_data = json.load(f)
            print(f"✅ Result file created:")
            for key, value in test_result_data.items():
                print(f"    {key}: {value}")
        else:
            print("❌ Result file not created")
        
        if result['success']:
            print("🎉 PACKAGE TEST PASSED!")
            return True
        else:
            print("❌ PACKAGE TEST FAILED!")
            return False
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"🧹 Cleaned up: {temp_dir}")


if __name__ == "__main__":
    success = test_package_installation()
    sys.exit(0 if success else 1)