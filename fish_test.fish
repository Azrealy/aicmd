#!/usr/bin/env fish
# Test script for Fish shell integration

function test_aicmd_fish
    echo "🐠 Testing AI Command Tool with Fish Shell"
    echo "=========================================="
    
    # Test 1: Check if integration is loaded
    echo ""
    echo "Test 1: Checking integration..."
    if functions -q fish_command_not_found
        echo "✓ fish_command_not_found function is defined"
    else
        echo "✗ fish_command_not_found function not found"
        echo "  Run: source ~/.aicmd/fish_integration.fish"
        return 1
    end
    
    if functions -q aicmd_capture_error
        echo "✓ aicmd_capture_error function is defined"
    else
        echo "✗ aicmd_capture_error function not found"
    end
    
    # Test 2: Check if aicmd command is available
    echo ""
    echo "Test 2: Checking aicmd command..."
    if command -v aicmd >/dev/null
        echo "✓ aicmd command is available"
    else
        echo "✗ aicmd command not found in PATH"
        echo "  Make sure aicmd is installed and in your PATH"
        return 1
    end
    
    # Test 3: Simulate command not found error
    echo ""
    echo "Test 3: Simulating command not found error..."
    
    # Create temp files as the integration would
    echo "fish: Unknown command: lls" > /tmp/aicmd_last_error
    echo "lls" > /tmp/aicmd_last_command
    echo "127" > /tmp/aicmd_last_exit_code
    echo "Command 'lls' not found" > /tmp/aicmd_simple_error
    
    echo "✓ Created simulation files"
    
    # List the temp files
    echo ""
    echo "Temporary files created:"
    for file in /tmp/aicmd_last_error /tmp/aicmd_last_command /tmp/aicmd_last_exit_code /tmp/aicmd_simple_error
        if test -f $file
            echo "  ✓ $file: "(cat $file)
        else
            echo "  ✗ $file: Not found"
        end
    end
    
    # Test 4: Test aicmd fix
    echo ""
    echo "Test 4: Testing 'aicmd fix'..."
    echo "Running: aicmd fix"
    echo "=================="
    
    aicmd fix
    
    echo ""
    echo "🎯 Manual Test Instructions:"
    echo "1. In a new Fish shell, try typing: lls"
    echo "2. You should see: fish: Unknown command: lls"
    echo "3. Then type: aicmd fix"
    echo "4. The AI should suggest: ls"
    echo ""
    echo "🔧 Enable auto-suggestions:"
    echo "set -gx AICMD_AUTO_SUGGEST 1"
    echo ""
    echo "Or use the alias:"
    echo "aicmd-enable-auto"
end

function clean_test_files
    echo "🧹 Cleaning up test files..."
    rm -f /tmp/aicmd_last_error /tmp/aicmd_last_command /tmp/aicmd_last_exit_code /tmp/aicmd_simple_error /tmp/aicmd_current_command
    echo "✓ Cleaned up"
end

# Check command line arguments
if test (count $argv) -gt 0
    switch $argv[1]
        case "clean"
            clean_test_files
        case "test"
            test_aicmd_fish
        case "*"
            echo "Usage: fish fish_test.fish [test|clean]"
    end
else
    test_aicmd_fish
end
