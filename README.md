# AI Command Tool 🤖

An intelligent command-line assistant that helps fix errors, suggests commands, and provides explanations using AI. Works seamlessly with any terminal including iTerm, and integrates with multiple AI providers.

## Features ✨

- **Error Fixing**: Automatically analyze and fix command errors
- **Command Suggestions**: Get command recommendations from natural language
- **Command Explanations**: Understand what commands do and how they work
- **Shell Integration**: Seamless integration with bash, zsh, and fish
- **Multiple AI Providers**: Support for OpenAI, Anthropic Claude, and custom endpoints
- **Safety Checks**: Built-in validation to prevent dangerous commands
- **Interactive Mode**: Conversational interface for extended assistance
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Quick Start 🚀

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd ai-command-tool
```

2. **Run the setup script:**

```bash
python3 setup.py
```

3. **Configure your API key:**

```bash
export OPENAI_API_KEY="your-openai-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### Basic Usage

```bash
# Fix a command error (with error message)
aicmd fix "ls: cannot access 'nonexistent': No such file or directory"

# Fix the last command error automatically (NEW!)
aicmd fix

# Get command suggestions
aicmd suggest "compress files in a directory"

# Explain a command
aicmd explain "find . -name '*.py' -exec grep -l 'import' {} \;"

# Interactive mode
aicmd --interactive
```

## Usage Examples 📚

### Automatic Error Detection (NEW!)

```bash
$ ls nonexistent-file
ls: cannot access 'nonexistent-file': No such file or directory

$ aicmd fix
🤖 Detected error: Command 'ls nonexistent-file' failed with exit code 2:
ls: cannot access 'nonexistent-file': No such file or directory

AI Response:
The error occurs because you're trying to list a file that doesn't exist. Here are some solutions:

COMMAND:
find . -name "*nonexistent*" -type f

This will search for files with similar names in the current directory.
```

### Command Suggestions

```bash
$ aicmd suggest "find large files"
🤖 AI Response:

To find large files in your system:

COMMAND:
find . -type f -size +100M -exec ls -lh {} \; | sort -k5 -hr

This finds files larger than 100MB and sorts them by size.
```

### Command Explanations

```bash
$ aicmd explain "tar -czf backup.tar.gz /home/user/documents"
🤖 AI Response:

This command creates a compressed archive:

BREAKDOWN:
- tar: Archive utility
- -c: Create new archive
- -z: Compress with gzip
- -f: Specify filename
- backup.tar.gz: Output filename
- /home/user/documents: Directory to archive

The command will create a gzip-compressed tar archive of the documents folder.
```

## Configuration ⚙️

Configuration file location: `~/.aicmd/config.json`

```json
{
  "openai_model": "gpt-3.5-turbo",
  "anthropic_model": "claude-3-sonnet-20240229",
  "max_tokens": 1000,
  "temperature": 0.1,
  "auto_execute": false,
  "verbose": false,
  "safety_checks": true,
  "cache_responses": true,
  "cache_duration": 3600,
  "terminal_integration": true,
  "shell_hooks": true
}
```

### API Configuration

#### Option 1: Environment Variables (Recommended)

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

#### Option 2: Configuration File

Add to `~/.aicmd/config.json`:

```json
{
  "openai_api_key": "your-openai-api-key",
  "anthropic_api_key": "your-anthropic-api-key"
}
```

#### Option 3: Custom Endpoint

For local LLMs or custom APIs:

```json
{
  "custom_endpoint": "http://localhost:11434/v1/completions",
  "custom_headers": {
    "Authorization": "Bearer your-token"
  }
}
```

## Shell Integration 🐚

The tool can integrate with your shell to provide automatic error suggestions:

### Bash Integration

Add to `~/.bashrc`:

```bash
source ~/.aicmd/bash_integration.sh
export AICMD_AUTO_SUGGEST=1
```

### Zsh Integration

Add to `~/.zshrc`:

```bash
source ~/.aicmd/zsh_integration.sh
export AICMD_AUTO_SUGGEST=1
```

### Fish Integration

Add to `~/.config/fish/config.fish`:

```bash
source ~/.aicmd/fish_integration.fish
set -gx AICMD_AUTO_SUGGEST 1
```

## Command Line Options 🔧

```bash
usage: aicmd [-h] [--interactive] [--config CONFIG] [--verbose] [--auto-execute]
             [action] [input_text ...]

AI-powered command assistant for fixing errors and providing advice

positional arguments:
  action            Action to perform (fix, suggest, explain, setup)
  input_text        Error message, command description, or command to explain

optional arguments:
  -h, --help        show this help message and exit
  --interactive, -i Start interactive mode
  --config CONFIG   Path to config file
  --verbose, -v     Enable verbose output
  --auto-execute    Automatically execute suggested commands (use with caution)
```

## Safety Features 🛡️

The tool includes built-in safety features:

- **Dangerous Command Detection**: Prevents execution of potentially harmful commands
- **User Confirmation**: Always asks before executing suggested commands
- **Safe Mode**: Commands are validated before suggestion
- **Audit Logging**: All actions can be logged for review

### Dangerous Commands Blocked

- `rm -rf /`
- `dd if=/dev/random of=/dev/sda`
- `:(){ :|:& };:` (fork bomb)
- `curl | sh` (arbitrary code execution)
- And many more...

## Interactive Mode 💬

Start an interactive session for extended assistance:

```bash
$ aicmd --interactive
AI Command Assistant - Interactive Mode
Type 'help' for commands, 'quit' to exit

aicmd> fix "npm install failed"
🤖 The npm install failure could be due to several reasons...

aicmd> suggest "backup my home directory"
🤖 To backup your home directory, you can use...

aicmd> help
Available commands:
  fix <error_message>     - Fix a command error
  suggest <description>   - Suggest a command for a task
  explain <command>       - Explain what a command does
  help                   - Show this help message
  quit/exit/q           - Exit interactive mode

aicmd> quit
```

## Troubleshooting 🔧

### Common Issues

**1. "No API key configured"**

```bash
# Set your API key
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

**2. "Command not found: aicmd"**

```bash
# Check if ~/.local/bin is in your PATH
echo $PATH
# Add it if missing
export PATH="$HOME/.local/bin:$PATH"
```

**3. "Permission denied"**

```bash
# Make the script executable
chmod +x ~/.local/share/aicmd/aicmd.py
```

**4. "Module not found: requests"**

```bash
# Install dependencies
pip install --user requests
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
aicmd --verbose fix "your error message"
```

## Advanced Usage 🎯

### Custom Prompts

The tool uses sophisticated prompts to provide context-aware assistance. The AI considers:

- Your operating system and shell
- Available command-line tools
- Current working directory
- Recent command history
- Environment variables

### Caching

Responses are cached to improve performance:

- Cache location: `~/.aicmd/cache/`
- Default duration: 1 hour
- Disable with: `"cache_responses": false`

### Logging

Enable logging for audit trails:

```json
{
  "log_file": "~/.aicmd/logs/aicmd.log",
  "verbose": true
}
```

## Architecture 🏗️

The tool is built with a modular architecture:

```
aicmd.py                 # Main entry point
├── core/
│   ├── command_processor.py    # Core logic
│   ├── ai_client.py           # AI API integration
│   └── config_manager.py      # Configuration handling
└── utils/
    ├── terminal_utils.py      # Terminal interaction
    ├── command_parser.py      # Command parsing
    ├── system_info.py         # System information
    └── logger.py              # Logging utilities
```

## Contributing 🤝

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Development Setup

```bash
git clone <repository-url>
cd ai-command-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

- Create an issue for bug reports
- Join discussions for feature requests
- Check the wiki for additional documentation

---

**Made with ❤️ for developers who love the command line**
