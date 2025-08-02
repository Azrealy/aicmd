#!/usr/bin/env python3
"""
Debug test script to check error detection
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_temp_files():
    """Test what's in the temporary files."""
    temp_files = [
        '/tmp/aicmd_last_error',
        '/tmp/aicmd_simple_error',
        '/tmp/aicmd_last_command',
        '/tmp/aicmd_last_exit_code'
    ]

    print("=== TEMP FILES DEBUG ===")
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    content = f.read().strip()
                    print(f"✓ {temp_file}: '{content}'")
            except Exception as e:
                print(f"✗ {temp_file}: Error reading - {e}")
        else:
            print(f"✗ {temp_file}: File not found")
    print()


def test_error_detection():
    """Test the error detection functions."""
    print("=== ERROR DETECTION DEBUG ===")

    from utils.logger import Logger
    from core.config_manager import ConfigManager
    from core.command_processor import CommandProcessor

    logger = Logger(verbose=True)
    config = ConfigManager()
    processor = CommandProcessor(config, logger)

    # Import the detection functions
    sys.path.append(str(project_root))
    from aicmd import detect_last_error

    error = detect_last_error(logger)
    if error:
        print(f"✓ Detected error: {error}")

        # Test command extraction
        from utils.command_parser import CommandParser
        parser = CommandParser()

        failed_command = parser.extract_command_from_error(error)
        print(f"✓ Extracted command: {failed_command}")

        error_category, extracted_info = parser.categorize_error(error)
        print(f"✓ Error category: {error_category}")
        print(f"✓ Extracted info: {extracted_info}")

    else:
        print("✗ No error detected")
    print()


def simulate_command_not_found():
    """Simulate a command not found error."""
    print("=== SIMULATING COMMAND NOT FOUND ===")

    # Create temporary files as if shell integration did it
    with open('/tmp/aicmd_last_error', 'w') as f:
        f.write("bash: lls: command not found")

    with open('/tmp/aicmd_last_command', 'w') as f:
        f.write("lls")

    with open('/tmp/aicmd_last_exit_code', 'w') as f:
        f.write("127")

    with open('/tmp/aicmd_simple_error', 'w') as f:
        f.write("Command 'lls' not found")

    print("✓ Created simulation files")

    # Now test detection
    test_temp_files()
    test_error_detection()


if __name__ == '__main__':
    print("AI Command Tool - Debug Test")
    print("=" * 40)

    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        simulate_command_not_found()
    else:
        test_temp_files()
        test_error_detection()

        if not any(os.path.exists(f) for f in ['/tmp/aicmd_last_error', '/tmp/aicmd_simple_error']):
            print("No temp files found. Try:")
            print("1. Run a command that fails (like 'lls')")
            print("2. Make sure shell integration is set up")
            print("3. Or run: python debug_test.py simulate")
