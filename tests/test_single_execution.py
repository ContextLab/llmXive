#!/usr/bin/env python3
"""
Single test to verify code execution works end-to-end
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from code_execution_manager import CodeExecutionManager


def test_single_execution():
    """Test a single code execution"""
    
    print("🧪 Single Code Execution Test")
    print("=" * 40)
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_single_"))
    print(f"📁 Test directory: {temp_dir}")
    
    try:
        # Create code execution manager
        manager = CodeExecutionManager(temp_dir)
        
        # Create project structure
        project_path = temp_dir / "test_project"
        code_dir = project_path / "code"
        code_dir.mkdir(parents=True)
        
        # Create simple test script
        test_script = code_dir / "main.py"
        test_script.write_text("""print("Hello from llmXive!")
print("Code execution is working!")

# Create a simple output file
with open("output.txt", "w") as f:
    f.write("Success!\\n")

print("Test complete")
""")
        
        print(f"📝 Created test script: {test_script}")
        
        # Execute the code
        print("🚀 Executing code...")
        
        result = manager.execute_code(project_path, test_script, timeout=60)
        
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
        
        # Check if output file was created
        output_file = project_path / "output.txt"
        if output_file.exists():
            print(f"✅ Output file created: {output_file.read_text().strip()}")
        else:
            print("❌ Output file not created")
        
        # Check execution reports
        json_report = project_path / "code" / "execution_report.json"
        md_report = project_path / "code" / "execution_report.md"
        
        print(f"📄 JSON report exists: {json_report.exists()}")
        print(f"📄 MD report exists: {md_report.exists()}")
        
        if result['success']:
            print("🎉 TEST PASSED!")
            return True
        else:
            print("❌ TEST FAILED!")
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
    success = test_single_execution()
    sys.exit(0 if success else 1)