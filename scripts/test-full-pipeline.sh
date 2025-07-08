#!/bin/bash

# llmXive Full Pipeline Test Script
# Tests the complete research pipeline from idea generation to publication

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLI_SCRIPT="$SCRIPT_DIR/llmxive-cli.py"
LOG_FILE="$PROJECT_ROOT/pipeline_test_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  llmXive Full Pipeline Test Suite   ${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to log and display messages
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function to check if API keys are set
check_api_keys() {
    log_message "INFO" "Checking API key configuration..."
    
    local missing_keys=()
    
    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        missing_keys+=("ANTHROPIC_API_KEY")
    fi
    
    if [[ -z "$OPENAI_API_KEY" ]]; then
        missing_keys+=("OPENAI_API_KEY")
    fi
    
    if [[ -z "$GOOGLE_API_KEY" ]]; then
        missing_keys+=("GOOGLE_API_KEY")
    fi
    
    if [[ ${#missing_keys[@]} -gt 0 ]]; then
        log_message "ERROR" "Missing API keys: ${missing_keys[*]}"
        log_message "ERROR" "Please set the following environment variables:"
        for key in "${missing_keys[@]}"; do
            log_message "ERROR" "  export $key='your_api_key_here'"
        done
        return 1
    fi
    
    log_message "SUCCESS" "All API keys are configured"
    return 0
}

# Function to test API connections
test_api_connections() {
    log_message "INFO" "Testing API connections..."
    
    if python3 "$CLI_SCRIPT" --test-apis; then
        log_message "SUCCESS" "API connection tests passed"
        return 0
    else
        log_message "ERROR" "API connection tests failed"
        return 1
    fi
}

# Function to run a single pipeline test
run_pipeline_test() {
    local test_name=$1
    local field=$2
    
    log_message "INFO" "Starting pipeline test: $test_name (field: $field)"
    
    local start_time=$(date +%s)
    
    if python3 "$CLI_SCRIPT" --field "$field" --base-path "$PROJECT_ROOT"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_message "SUCCESS" "Pipeline test '$test_name' completed in ${duration}s"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_message "ERROR" "Pipeline test '$test_name' failed after ${duration}s"
        return 1
    fi
}

# Function to verify pipeline outputs
verify_pipeline_outputs() {
    local project_id=$1
    
    log_message "INFO" "Verifying pipeline outputs for project: $project_id"
    
    local required_files=(
        "technical_design_documents/$project_id/design.md"
        "implementation_plans/$project_id/plan.md"
        "code/$project_id/main.py"
        "data/$project_id/README.md"
        "papers/$project_id/paper.tex"
    )
    
    local all_exist=true
    
    for file in "${required_files[@]}"; do
        local full_path="$PROJECT_ROOT/$file"
        if [[ -f "$full_path" ]]; then
            local file_size=$(wc -c < "$full_path")
            log_message "SUCCESS" "✓ $file exists (${file_size} bytes)"
        else
            log_message "ERROR" "✗ $file missing"
            all_exist=false
        fi
    done
    
    if $all_exist; then
        log_message "SUCCESS" "All required files exist for project $project_id"
        return 0
    else
        log_message "ERROR" "Some required files missing for project $project_id"
        return 1
    fi
}

# Function to analyze paper quality
analyze_paper_quality() {
    local paper_path=$1
    
    log_message "INFO" "Analyzing paper quality: $paper_path"
    
    if [[ ! -f "$paper_path" ]]; then
        log_message "ERROR" "Paper file not found: $paper_path"
        return 1
    fi
    
    local word_count=$(wc -w < "$paper_path")
    local line_count=$(wc -l < "$paper_path")
    
    log_message "INFO" "Paper statistics:"
    log_message "INFO" "  - Word count: $word_count"
    log_message "INFO" "  - Line count: $line_count"
    
    # Check for required sections
    local required_sections=("Abstract" "Introduction" "Methods" "Results" "Discussion" "References")
    local sections_found=0
    
    for section in "${required_sections[@]}"; do
        if grep -qi "$section" "$paper_path"; then
            log_message "SUCCESS" "  ✓ Found section: $section"
            ((sections_found++))
        else
            log_message "WARNING" "  ✗ Missing section: $section"
        fi
    done
    
    log_message "INFO" "Sections found: $sections_found/${#required_sections[@]}"
    
    # Check for potential quality issues
    if grep -qi "hallucinated\|fabricated\|placeholder" "$paper_path"; then
        log_message "WARNING" "Potential quality issues detected in paper"
    fi
    
    # Basic quality assessment
    if [[ $word_count -gt 2000 && $sections_found -ge 4 ]]; then
        log_message "SUCCESS" "Paper appears to meet basic quality criteria"
        return 0
    else
        log_message "WARNING" "Paper may not meet quality criteria (words: $word_count, sections: $sections_found)"
        return 1
    fi
}

# Function to create GitHub secrets (informational)
show_github_secrets_instructions() {
    log_message "INFO" "GitHub Secrets Configuration Instructions:"
    echo ""
    echo "To add API keys as GitHub secrets for automated workflows:"
    echo ""
    echo "1. Go to your GitHub repository"
    echo "2. Click Settings → Secrets and variables → Actions"
    echo "3. Click 'New repository secret'"
    echo "4. Add the following secrets:"
    echo ""
    echo "   Name: ANTHROPIC_API_KEY"
    echo "   Value: [your Anthropic API key]"
    echo ""
    echo "   Name: OPENAI_API_KEY"
    echo "   Value: [your OpenAI API key]"
    echo ""
    echo "   Name: GOOGLE_API_KEY"
    echo "   Value: [your Google API key]"
    echo ""
    echo "5. These will be available in GitHub Actions as:"
    echo "   \${{ secrets.ANTHROPIC_API_KEY }}"
    echo "   \${{ secrets.OPENAI_API_KEY }}"
    echo "   \${{ secrets.GOOGLE_API_KEY }}"
    echo ""
}

# Function to run comprehensive pipeline tests
run_comprehensive_tests() {
    log_message "INFO" "Starting comprehensive pipeline tests..."
    
    local test_fields=("biology" "computer science" "physics")
    local successful_tests=0
    local total_tests=${#test_fields[@]}
    
    for field in "${test_fields[@]}"; do
        log_message "INFO" "Running test for field: $field"
        
        if run_pipeline_test "Test_$field" "$field"; then
            ((successful_tests++))
            
            # Try to find the most recent project for this field
            local latest_project=$(find "$PROJECT_ROOT/papers" -maxdepth 1 -type d -name "*pipeline-test*" | sort | tail -1)
            if [[ -n "$latest_project" ]]; then
                local project_id=$(basename "$latest_project")
                verify_pipeline_outputs "$project_id"
                
                local paper_file="$latest_project/paper.tex"
                if [[ -f "$paper_file" ]]; then
                    analyze_paper_quality "$paper_file"
                fi
            fi
        fi
        
        log_message "INFO" "Completed test for field: $field"
        echo ""
    done
    
    log_message "INFO" "Test Summary: $successful_tests/$total_tests tests successful"
    
    if [[ $successful_tests -eq $total_tests ]]; then
        log_message "SUCCESS" "All pipeline tests completed successfully!"
        return 0
    else
        log_message "WARNING" "Some pipeline tests failed"
        return 1
    fi
}

# Main execution flow
main() {
    log_message "INFO" "Starting llmXive pipeline test suite"
    log_message "INFO" "Log file: $LOG_FILE"
    log_message "INFO" "Project root: $PROJECT_ROOT"
    
    # Pre-flight checks
    if ! check_api_keys; then
        log_message "ERROR" "API key configuration failed"
        show_github_secrets_instructions
        exit 1
    fi
    
    if ! test_api_connections; then
        log_message "ERROR" "API connection tests failed"
        exit 1
    fi
    
    log_message "SUCCESS" "Pre-flight checks completed"
    echo ""
    
    # Run comprehensive tests
    if run_comprehensive_tests; then
        log_message "SUCCESS" "🎉 All pipeline tests completed successfully!"
        
        # Final verification
        log_message "INFO" "Final verification..."
        
        local paper_count=$(find "$PROJECT_ROOT/papers" -name "paper.tex" | wc -l)
        log_message "INFO" "Total papers generated: $paper_count"
        
        local latest_papers=$(find "$PROJECT_ROOT/papers" -name "paper.tex" -newer "$PROJECT_ROOT/pipeline_log.txt" 2>/dev/null | head -3)
        if [[ -n "$latest_papers" ]]; then
            log_message "SUCCESS" "Recent papers generated:"
            echo "$latest_papers" | while read -r paper; do
                log_message "SUCCESS" "  📄 $paper"
            done
        fi
        
        echo ""
        log_message "INFO" "🚀 Pipeline is ready for production deployment!"
        log_message "INFO" "📋 See $LOG_FILE for detailed execution log"
        
        exit 0
    else
        log_message "ERROR" "❌ Some pipeline tests failed"
        log_message "ERROR" "📋 See $LOG_FILE for detailed error information"
        exit 1
    fi
}

# Run main function
main "$@"