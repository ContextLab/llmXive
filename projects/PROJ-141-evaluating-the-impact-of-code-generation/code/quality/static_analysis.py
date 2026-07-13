"""
Static analysis warning count using pylint (Python) or checkstyle (Java).

This module implements FR-031: Static Analysis Warning Count.
It analyzes code submissions for warnings using:
- pylint for Python code
- checkstyle for Java code

Returns the count of warnings/errors detected.
"""
import os
import sys
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class StaticAnalysisError(Exception):
    """Custom exception for static analysis failures."""
    pass

def run_pylint(code_content: str, temp_dir: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
    """
    Run pylint on Python code and return warning count.
    
    Args:
        code_content: The Python code as a string
        temp_dir: Optional directory for temporary files
        
    Returns:
        Tuple of (warning_count, details_dict)
        
    Raises:
        StaticAnalysisError: If pylint fails unexpectedly
    """
    try:
        # Create temporary file for the code
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False, 
            dir=temp_dir
        ) as tmp_file:
            tmp_file.write(code_content)
            tmp_path = tmp_file.name

        try:
            # Run pylint with specific output format (JSON)
            # --disable=all --enable=W,E: Only enable warnings and errors
            # --output-format=json: Machine-readable output
            result = subprocess.run(
                [
                    sys.executable, '-m', 'pylint',
                    '--disable=all',
                    '--enable=W,E',
                    '--output-format=json',
                    tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=60,
                env=os.environ.copy()
            )
            
            # Parse pylint output
            try:
                # Pylint might output JSON or error messages
                output = result.stdout.strip()
                if output:
                    messages = json.loads(output)
                    if isinstance(messages, list):
                        warning_count = len(messages)
                        details = {
                            'tool': 'pylint',
                            'language': 'python',
                            'total_issues': warning_count,
                            'messages': messages,
                            'exit_code': result.returncode
                        }
                    else:
                        warning_count = 0
                        details = {
                            'tool': 'pylint',
                            'language': 'python',
                            'total_issues': 0,
                            'messages': [],
                            'exit_code': result.returncode
                        }
                else:
                    warning_count = 0
                    details = {
                        'tool': 'pylint',
                        'language': 'python',
                        'total_issues': 0,
                        'messages': [],
                        'exit_code': result.returncode,
                        'stderr': result.stderr
                    }
            except json.JSONDecodeError:
                # Fallback: if JSON parsing fails, try to count issues from text
                lines = result.stdout.strip().split('\n')
                warning_count = sum(
                    1 for line in lines 
                    if line and ('warning' in line.lower() or 'error' in line.lower())
                )
                details = {
                    'tool': 'pylint',
                    'language': 'python',
                    'total_issues': warning_count,
                    'raw_output': result.stdout,
                    'stderr': result.stderr
                }
            
            return warning_count, details

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except subprocess.TimeoutExpired:
        logger.warning(f"pylint analysis timed out")
        return 0, {
            'tool': 'pylint',
            'language': 'python',
            'error': 'timeout',
            'total_issues': 0
        }
    except Exception as e:
        logger.error(f"pylint analysis failed: {str(e)}")
        raise StaticAnalysisError(f"pylint execution failed: {str(e)}")

def run_checkstyle(code_content: str, temp_dir: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
    """
    Run checkstyle on Java code and return warning count.
    
    Args:
        code_content: The Java code as a string
        temp_dir: Optional directory for temporary files
        
    Returns:
        Tuple of (warning_count, details_dict)
        
    Raises:
        StaticAnalysisError: If checkstyle fails unexpectedly
    """
    try:
        # Create temporary file for the code
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.java', 
            delete=False, 
            dir=temp_dir
        ) as tmp_file:
            tmp_file.write(code_content)
            tmp_path = tmp_file.name

        try:
            # Check if checkstyle is available
            checkstyle_path = os.environ.get('CHECKSTYLE_PATH', 'checkstyle')
            
            # Try to run checkstyle with a basic config
            # We use a simple config that checks for common issues
            config_xml = """
            <!DOCTYPE module PUBLIC
                "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
                "https://checkstyle.org/dtds/configuration_1_3.dtd">
            <module name="Checker">
                <module name="TreeWalker">
                    <module name="AvoidStarImport"/>
                    <module name="UnusedImports"/>
                    <module name="RedundantImport"/>
                    <module name="MethodName"/>
                    <module name="PackageName"/>
                    <module name="ParameterName"/>
                    <module name="LocalVariableName"/>
                    <module name="MemberName"/>
                    <module name="ClassTypeParameterName"/>
                    <module name="MethodTypeParameterName"/>
                    <module name="InterfaceTypeParameterName"/>
                    <module name="ConstantName"/>
                    <module name="StaticVariableName"/>
                    <module name="TypeName"/>
                    <module name="IllegalIdentifierName"/>
                    <module name="PatternVariableName"/>
                    <module name="RecordComponentName"/>
                    <module name="RecordComponentNumber"/>
                    <module name="LambdaParameterName"/>
                    <module name="CatchParameterName"/>
                    <module name="LocalFinalVariableName"/>
                    <module name="NoWhitespaceAfter"/>
                    <module name="NoWhitespaceBefore"/>
                    <module name="OperatorWrap"/>
                    <module name="ParenPad"/>
                    <module name="TypecastParenPad"/>
                    <module name="WhitespaceAfter"/>
                    <module name="WhitespaceAround"/>
                    <module name="ModifierOrder"/>
                    <module name="RedundantModifier"/>
                    <module name="AvoidNestedBlocks"/>
                    <module name="EmptyBlock"/>
                    <module name="NeedBraces"/>
                    <module name="LeftCurly"/>
                    <module name="RightCurly"/>
                    <module name="EmptyStatement"/>
                    <module name="EqualsHashCode"/>
                    <module name="IllegalInstantiation"/>
                    <module name="InnerAssignment"/>
                    <module name="MagicNumber"/>
                    <module name="MissingSwitchDefault"/>
                    <module name="MultipleVariableDeclarations"/>
                    <module name="SimplifyBooleanExpression"/>
                    <module name="SimplifyBooleanReturn"/>
                    <module name="DefaultComesLast"/>
                    <module name="FallThrough"/>
                    <module name="OneStatementPerLine"/>
                    <module name="StringLiteralEquality"/>
                    <module name="NestedForDepth"/>
                    <module name="NestedIfDepth"/>
                    <module name="NestedTryDepth"/>
                    <module name="MultipleStringLiterals"/>
                    <module name="UnnecessaryParentheses"/>
                    <module name="UnnecessarySemicolonAfterOuterTypeDeclaration"/>
                    <module name="UnnecessarySemicolonAfterTypeMemberDeclaration"/>
                    <module name="UnnecessarySemicolonInEnumeration"/>
                    <module name="UnnecessarySemicolonInTryWithResources"/>
                    <module name="ArrayTypeStyle"/>
                    <module name="FinalParameters"/>
                    <module name="GenericWhitespace"/>
                    <module name="CommentsIndentation"/>
                    <module name="Translation"/>
                    <module name="OuterTypeFilename"/>
                    <module name="IllegalToken"/>
                    <module name="IllegalTokenText"/>
                    <module name="IllegalType"/>
                    <module name="ModifiedControlVariable"/>
                    <module name="MutableException"/>
                    <module name="ThrowsCount"/>
                    <module name="VisibilityModifier"/>
                    <module name="FinalClass"/>
                    <module name="HideUtilityClassConstructor"/>
                    <module name="InterfaceIsType"/>
                    <module name="MutableException"/>
                    <module name="ThrowsCount"/>
                    <module name="CovariantEquals"/>
                    <module name="ExceptionAsParameterName"/>
                    <module name="ParameterAssignment"/>
                    <module name="OverloadMethodsDeclarationOrder"/>
                    <module name="VariableDeclarationUsageDistance"/>
                    <module name="MethodCount"/>
                    <module name="OuterTypeNumber"/>
                    <module name="EmptyLineSeparator"/>
                    <module name="NoLineWrap"/>
                    <module name="SeparatorWrap"/>
                    <module name="NoEnumTrailingComma"/>
                    <module name="AnnotationLocation"/>
                    <module name="AnnotationOnSameLine"/>
                    <module name="AnnotationUseStyle"/>
                    <module name="MissingDeprecated"/>
                    <module name="MissingOverride"/>
                    <module name="PackageAnnotation"/>
                    <module name="SuppressWarnings"/>
                    <module name="SuppressWarningsHolder"/>
                    <module name="AnnotationLocation"/>
                    <module name="NeedBraces"/>
                    <module name="EmptyForInitializerPad"/>
                    <module name="EmptyForIteratorPad"/>
                    <module name="MethodParamPad"/>
                    <module name="NoWhitespaceAfter"/>
                    <module name="NoWhitespaceBefore"/>
                    <module name="OperatorWrap"/>
                    <module name="ParenPad"/>
                    <module name="TypecastParenPad"/>
                    <module name="WhitespaceAfter"/>
                    <module name="WhitespaceAround"/>
                    <module name="SingleSpaceSeparator"/>
                    <module name="ValidateDefaultParameters"/>
                    <module name="GenericWhitespace"/>
                    <module name="CommentsIndentation"/>
                </module>
                <module name="NewlineAtEndOfFile"/>
                <module name="FileLength"/>
                <module name="LineLength">
                    <property name="max" value="120"/>
                </module>
                <module name="FileTabCharacter"/>
                <module name="RegexpSingleline">
                    <property name="format" value="\s+$"/>
                    <property name="message" value="Trailing whitespace"/>
                </module>
            </module>
            """
            
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.xml', 
                delete=False,
                dir=temp_dir
            ) as config_file:
                config_file.write(config_xml)
                config_path = config_file.name

            try:
                # Run checkstyle
                result = subprocess.run(
                    [
                        'java', '-jar', checkstyle_path,
                        '-c', config_path,
                        tmp_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=os.environ.copy()
                )
                
                # Parse checkstyle XML output
                # Checkstyle outputs XML by default when using -c
                import xml.etree.ElementTree as ET
                
                try:
                    root = ET.fromstring(result.stdout)
                    warnings = []
                    for file_elem in root.findall('file'):
                        for error_elem in file_elem.findall('error'):
                            warnings.append({
                                'line': error_elem.get('line'),
                                'column': error_elem.get('column'),
                                'severity': error_elem.get('severity'),
                                'message': error_elem.get('message'),
                                'source': error_elem.get('source')
                            })
                    
                    warning_count = len(warnings)
                    details = {
                        'tool': 'checkstyle',
                        'language': 'java',
                        'total_issues': warning_count,
                        'messages': warnings,
                        'exit_code': result.returncode
                    }
                except ET.ParseError:
                    # Fallback: try to parse text output
                    lines = result.stdout.strip().split('\n')
                    warning_count = sum(
                        1 for line in lines 
                        if line and ('error' in line.lower() or 'warning' in line.lower())
                    )
                    details = {
                        'tool': 'checkstyle',
                        'language': 'java',
                        'total_issues': warning_count,
                        'raw_output': result.stdout,
                        'stderr': result.stderr
                    }
                
                return warning_count, details

            finally:
                if os.path.exists(config_path):
                    os.unlink(config_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except subprocess.TimeoutExpired:
        logger.warning(f"checkstyle analysis timed out")
        return 0, {
            'tool': 'checkstyle',
            'language': 'java',
            'error': 'timeout',
            'total_issues': 0
        }
    except FileNotFoundError:
        logger.warning(f"checkstyle not found, skipping Java analysis")
        return 0, {
            'tool': 'checkstyle',
            'language': 'java',
            'error': 'not_found',
            'total_issues': 0
        }
    except Exception as e:
        logger.error(f"checkstyle analysis failed: {str(e)}")
        raise StaticAnalysisError(f"checkstyle execution failed: {str(e)}")

def detect_language(code_content: str) -> str:
    """
    Detect programming language from code content.
    
    Args:
        code_content: The code as a string
        
    Returns:
        'python', 'java', or 'unknown'
    """
    # Simple heuristics for language detection
    content = code_content.strip()
    
    # Check for Java indicators
    java_indicators = [
        'public class', 'private class', 'protected class',
        'public static void main', 'import java.',
        'package ', '@Override', 'extends ', 'implements '
    ]
    
    # Check for Python indicators
    python_indicators = [
        'import ', 'from ', 'def ', 'class ', 
        'if __name__ ==', 'print(', 'async def', 'await '
    ]
    
    content_lower = content.lower()
    
    java_score = sum(1 for indicator in java_indicators if indicator.lower() in content_lower)
    python_score = sum(1 for indicator in python_indicators if indicator.lower() in content_lower)
    
    if java_score > python_score and java_score > 0:
        return 'java'
    elif python_score > java_score and python_score > 0:
        return 'python'
    else:
        # Fallback: check file extension if available in content
        if '.java' in content or 'public class' in content:
            return 'java'
        elif '.py' in content or 'def ' in content:
            return 'python'
        return 'unknown'

def analyze_static_warnings(
    code_content: str,
    language: Optional[str] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Analyze code for static analysis warnings.
    
    Args:
        code_content: The code to analyze
        language: Optional language hint ('python' or 'java')
        
    Returns:
        Tuple of (warning_count, details_dict)
        
    Raises:
        StaticAnalysisError: If analysis fails
    """
    if not code_content or not code_content.strip():
        return 0, {
            'tool': 'none',
            'language': 'unknown',
            'total_issues': 0,
            'message': 'Empty code content'
        }
    
    # Detect language if not provided
    if language is None:
        language = detect_language(code_content)
    
    logger.info(f"Analyzing code with detected language: {language}")
    
    if language == 'python':
        return run_pylint(code_content)
    elif language == 'java':
        return run_checkstyle(code_content)
    else:
        # Unknown language - return 0 warnings
        logger.warning(f"Unknown language: {language}, skipping static analysis")
        return 0, {
            'tool': 'none',
            'language': language,
            'total_issues': 0,
            'message': f'No static analysis available for language: {language}'
        }

def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Static analysis warning count for code submissions'
    )
    parser.add_argument(
        'code_file',
        nargs='?',
        help='Path to code file to analyze'
    )
    parser.add_argument(
        '--language',
        choices=['python', 'java'],
        help='Programming language (auto-detected if not specified)'
    )
    parser.add_argument(
        '--output',
        help='Output file for JSON results (default: stdout)'
    )
    
    args = parser.parse_args()
    
    if not args.code_file:
        parser.print_help()
        sys.exit(1)
    
    try:
        with open(args.code_file, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        warning_count, details = analyze_static_warnings(
            code_content,
            language=args.language
        )
        
        result = {
            'warning_count': warning_count,
            'details': details,
            'file': args.code_file
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(result, indent=2))
        
        sys.exit(0 if warning_count == 0 else 1)
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.code_file}", file=sys.stderr)
        sys.exit(2)
    except StaticAnalysisError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(4)

if __name__ == '__main__':
    main()