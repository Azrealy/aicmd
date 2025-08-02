#!/usr/bin/env python3
"""
Setup script for AI Command Tool
Installs the tool and sets up shell integration
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    print("🚀 Setting up AI Command Tool...")

    # Get installation directory
    install_dir = get_install_directory()
    print(f"Installing to: {install_dir}")

    # Create installation directory
    install_dir.mkdir(parents=True, exist_ok=True)

    # Copy files
    copy_project_files(install_dir)

    # Make main script executable
    main_script = install_dir / 'aicmd.py'
    make_executable(main_script)

    # Create symlink or add to PATH
    setup_command_access(install_dir, main_script)

    # Setup configuration
    setup_configuration()

    # Setup shell integration
    setup_shell_integration()

    # Install dependencies
    install_dependencies()

    print("✅ Installation complete!")
    print("\nTo get started:")
    print("1. Set your API key: export OPENAI_API_KEY='your-key' or ANTHROPIC_API_KEY='your-key'")
    print("2. Try: aicmd suggest 'list files'")
    print("3. For help: aicmd --help")


def get_install_directory():
    """Get the installation directory."""
    # Try user's local bin directory first
    local_bin = Path.home() / '.local' / 'bin'
    if local_bin.exists() or can_create_directory(local_bin):
        return Path.home() / '.local' / 'share' / 'aicmd'

    # Fallback to user's home directory
    return Path.home() / '.aicmd'


def can_create_directory(path):
    """Check if we can create a directory."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError:
        return False


def copy_project_files(install_dir):
    """Copy project files to installation directory."""
    print("📁 Copying project files...")

    # Files to copy (relative to current directory)
    files_to_copy = [
        'aicmd.py',
        'core/command_processor.py',
        'core/ai_client.py',
        'core/config_manager.py',
        'utils/terminal_utils.py',
        'utils/command_parser.py',
        'utils/system_info.py',
        'utils/logger.py'
    ]

    current_dir = Path(__file__).parent

    for file_path in files_to_copy:
        src = current_dir / file_path
        dst = install_dir / file_path

        # Create directory if it doesn't exist
        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.exists():
            shutil.copy2(src, dst)
            print(f"  ✓ {file_path}")
        else:
            print(f"  ⚠ Warning: {file_path} not found")


def make_executable(script_path):
    """Make script executable."""
    try:
        current_mode = script_path.stat().st_mode
        script_path.chmod(current_mode | 0o755)
        print(f"✓ Made {script_path.name} executable")
    except Exception as e:
        print(f"⚠ Could not make {script_path.name} executable: {e}")


def setup_command_access(install_dir, main_script):
    """Setup command access via symlink or PATH."""
    print("🔗 Setting up command access...")

    # Try to create symlink in user's local bin
    local_bin = Path.home() / '.local' / 'bin'

    if local_bin.exists() or can_create_directory(local_bin):
        symlink_path = local_bin / 'aicmd'

        try:
            # Remove existing symlink if it exists
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # Create new symlink
            symlink_path.symlink_to(main_script)
            print(f"✓ Created symlink: {symlink_path} -> {main_script}")

            # Check if ~/.local/bin is in PATH
            path = os.getenv('PATH', '')
            if str(local_bin) not in path:
                print(f"⚠ Add {local_bin} to your PATH for global access")
                print(
                    f"  Add this to your shell config: export PATH=\"{local_bin}:$PATH\"")

            return

        except Exception as e:
            print(f"⚠ Could not create symlink: {e}")

    # Fallback: provide instructions for manual setup
    print("ℹ To use 'aicmd' command globally, add this alias to your shell config:")
    print(f"  alias aicmd='{main_script}'")


def setup_configuration():
    """Setup initial configuration."""
    print("⚙️ Setting up configuration...")

    config_dir = Path.home() / '.aicmd'
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / 'config.json'

    if not config_file.exists():
        default_config = {
            "openai_model": "gpt-4o-mini",
            "anthropic_model": "claude-3-sonnet-20240229",
            "max_tokens": 4096,
            "temperature": 1,
            "auto_execute": False,
            "verbose": False,
            "safety_checks": True,
            "cache_responses": True,
            "cache_duration": 3600,
            "terminal_integration": True,
            "shell_hooks": True
        }

        import json
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"✓ Created default config: {config_file}")
    else:
        print(f"✓ Config already exists: {config_file}")


def setup_shell_integration():
    """Setup shell integration."""
    print("🐚 Setting up shell integration...")

    shell = os.getenv('SHELL', '/bin/bash')
    shell_name = Path(shell).name

    integration_dir = Path.home() / '.aicmd'
    integration_file = integration_dir / f'{shell_name}_integration.sh'

    # Generate integration script
    if shell_name == 'bash':
        integration_code = '''
# AI Command Tool Integration for Bash
export AICMD_SHELL="bash"

# Error handler function
aicmd_error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        local last_command=$(fc -ln -1 2>/dev/null | sed 's/^[ \t]*//')
        if [ -n "$last_command" ]; then
            echo "💡 Suggestion: aicmd fix \"$last_command failed with exit code $exi
t_code\""
        fi
    fi
    return $exit_code
}

# Command not found handler
command_not_found_handle() {
    if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        echo "💡 Try: aicmd fix \"Command not found: $1\""
    fi
    echo "bash: $1: command not found"
    return 127
}

# Optional: Enable auto-suggestions
# export AICMD_AUTO_SUGGEST=1
'''

    elif shell_name == 'zsh':
        integration_code = '''
# AI Command Tool Integration for Zsh
export AICMD_SHELL="zsh"

# Error handler function
aicmd_error_handler() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        local last_command=$(fc -ln -1 2>/dev/null)
        if [ -n "$last_command" ]; then
d failed with exit code $exit_code\""
        fi
    fi
    return $exit_code
}

# Command not found handler
command_not_found_handler() {
    if [ "$AICMD_AUTO_SUGGEST" = "1" ]; then
        echo "💡 Try: aicmd fix \"Command not found: $1\""
    fi
    echo "zsh: command not found: $1"
    return 127
}

# Optional: Enable auto-suggestions
# export AICMD_AUTO_SUGGEST=1
'''

    elif shell_name == 'fish':
        integration_code = '''
# AI Command Tool Integration for Fish
set -gx AICMD_SHELL "fish"

# Command not found handler
function fish_command_not_found
    if test "$AICMD_AUTO_SUGGEST" = "1"
        echo "💡 Try: aicmd fix \"Command not found: $argv[1]\""
    end
    echo "fish: Unknown command: $argv[1]"
end

# set -gx AICMD_AUTO_SUGGEST 1
'''

    else:
        integration_code = f'# AI Command Tool: Shell "{shell_name}" integration not available'

    # Write integration file
    with open(integration_file, 'w') as f:
        f.write(integration_code)

    print(f"✓ Created shell integration: {integration_file}")
    print(f"📝 To enable integration, add to your shell config:")

    if shell_name == 'bash':
        config_file = Path.home() / '.bashrc'
        print(f"  echo 'source {integration_file}' >> {config_file}")
    elif shell_name == 'zsh':
        config_file = Path.home() / '.zshrc'
        print(f"  echo 'source {integration_file}' >> {config_file}")
    elif shell_name == 'fish':
        config_file = Path.home() / '.config' / 'fish' / 'config.fish'
        print(f"  echo 'source {integration_file}' >> {config_file}")


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")

    dependencies = ['requests']

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} already installed")
        except ImportError:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip',
                                      'install', '--user', dep])
                print(f"✓ Installed {dep}")
            except subprocess.CalledProcessError:
                print(
                    f"⚠ Failed to install {dep}. Please install manually: pip install {dep}")


def check_system_requirements():
    """Check system requirements."""
    print("🔍 Checking system requirements...")

    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 6):
        print("❌ Python 3.6 or higher is required")
        sys.exit(1)
    else:
        print(
            f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

    # Check for pip
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', '--version'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ pip is available")
    except subprocess.CalledProcessError:
        print("⚠ pip not found. Some features may not work.")

    return True


if __name__ == '__main__':
    try:
        if not check_system_requirements():
            sys.exit(1)
        main()
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation failed: {e}")

#            echo "💡 Suggestion: aicmd fix \"$last_comman
