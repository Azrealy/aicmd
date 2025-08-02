"""
System Information Collector - Gathers system context for AI prompts
"""

import os
import platform
import subprocess
import shutil
from typing import Dict, List
from pathlib import Path


class SystemInfo:
    """Collects system information to provide context for AI assistance."""

    def __init__(self):
        self._cached_info = {}

    def get_os_info(self) -> str:
        """Get operating system information."""
        if 'os_info' not in self._cached_info:
            try:
                system = platform.system()
                release = platform.release()
                version = platform.version()

                if system == "Linux":
                    # Try to get distribution info
                    try:
                        with open('/etc/os-release', 'r') as f:
                            lines = f.readlines()
                            for line in lines:
                                if line.startswith('PRETTY_NAME='):
                                    distro = line.split(
                                        '=')[1].strip().strip('"')
                                    self._cached_info['os_info'] = f"{distro} ({system} {release})"
                                    break
                            else:
                                self._cached_info['os_info'] = f"{system} {release}"
                    except FileNotFoundError:
                        self._cached_info['os_info'] = f"{system} {release}"

                elif system == "Darwin":
                    # macOS
                    try:
                        mac_version = subprocess.check_output(
                            ['sw_vers', '-productVersion'], text=True).strip()
                        self._cached_info['os_info'] = f"macOS {mac_version}"
                    except subprocess.CalledProcessError:
                        self._cached_info['os_info'] = f"macOS {release}"

                elif system == "Windows":
                    self._cached_info['os_info'] = f"Windows {release}"

                else:
                    self._cached_info['os_info'] = f"{system} {release}"

            except Exception:
                self._cached_info['os_info'] = "Unknown OS"

        return self._cached_info['os_info']

    def get_shell_info(self) -> str:
        """Get shell information."""
        if 'shell_info' not in self._cached_info:
            shell = os.getenv('SHELL', '/bin/bash')
            shell_name = Path(shell).name

            try:
                # Try to get shell version
                if shell_name == 'bash':
                    result = subprocess.run(
                        ['bash', '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        version_line = result.stdout.split('\n')[0]
                        self._cached_info['shell_info'] = version_line
                    else:
                        self._cached_info['shell_info'] = shell_name

                elif shell_name == 'zsh':
                    result = subprocess.run(
                        ['zsh', '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self._cached_info['shell_info'] = result.stdout.strip()
                    else:
                        self._cached_info['shell_info'] = shell_name

                elif shell_name == 'fish':
                    result = subprocess.run(
                        ['fish', '--version'], capture_output=True, text=True)
                    if result.returncode == 0:
                        self._cached_info['shell_info'] = result.stdout.strip()
                    else:
                        self._cached_info['shell_info'] = shell_name

                else:
                    self._cached_info['shell_info'] = shell_name

            except Exception:
                self._cached_info['shell_info'] = shell_name

        return self._cached_info['shell_info']

    def get_available_tools(self) -> List[str]:
        """Get list of available command-line tools."""
        if 'available_tools' not in self._cached_info:
            common_tools = [
                'git', 'docker', 'kubectl', 'helm',
                'python', 'python3', 'pip', 'pip3',
                'node', 'npm', 'yarn', 'pnpm',
                'go', 'cargo', 'rustc',
                'java', 'javac', 'maven', 'gradle',
                'gcc', 'g++', 'make', 'cmake',
                'curl', 'wget', 'ssh', 'scp', 'rsync',
                'vim', 'nano', 'emacs', 'code',
                'grep', 'sed', 'awk', 'jq',
                'tar', 'zip', 'unzip', 'gzip',
                'systemctl', 'service', 'brew',
                'apt', 'apt-get', 'yum', 'dnf', 'pacman',
                'ps', 'top', 'htop', 'kill', 'killall',
                'find', 'locate', 'which', 'whereis',
                'cat', 'less', 'more', 'head', 'tail',
                'ls', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv',
                'chmod', 'chown', 'chgrp',
                'mount', 'umount', 'df', 'du', 'free',
                'history', 'alias', 'export', 'env',
                'screen', 'tmux', 'nohup',
                'crontab', 'at', 'jobs', 'bg', 'fg'
            ]

            available = []
            for tool in common_tools:
                if shutil.which(tool):
                    available.append(tool)

            self._cached_info['available_tools'] = available

        return self._cached_info['available_tools']

    def get_recent_commands(self, limit: int = 5) -> List[str]:
        """Get recent commands from history."""
        if 'recent_commands' not in self._cached_info:
            commands = []
            shell = Path(os.getenv('SHELL', '/bin/bash')).name

            try:
                if shell == 'bash':
                    hist_file = os.getenv(
                        'HISTFILE', os.path.expanduser('~/.bash_history'))
                elif shell == 'zsh':
                    hist_file = os.getenv(
                        'HISTFILE', os.path.expanduser('~/.zsh_history'))
                elif shell == 'fish':
                    # Fish uses a different approach
                    result = subprocess.run(['fish', '-c', f'history --max={limit}'],
                                            capture_output=True, text=True)
                    if result.returncode == 0:
                        commands = result.stdout.strip().split('\n')
                    hist_file = None
                else:
                    hist_file = None

                if hist_file and os.path.exists(hist_file):
                    with open(hist_file, 'r') as f:
                        lines = f.readlines()
                        # Get last N lines, clean them up
                        for line in lines[-limit:]:
                            line = line.strip()
                            # Handle zsh history format (timestamp;command)
                            if ';' in line and shell == 'zsh':
                                line = line.split(';', 1)[1]
                            if line and not line.startswith('#'):
                                commands.append(line)

            except Exception:
                commands = []

            self._cached_info['recent_commands'] = commands[-limit:]

        return self._cached_info['recent_commands']

    def get_environment_variables(self) -> Dict[str, str]:
        """Get relevant environment variables."""
        relevant_vars = [
            'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'LC_ALL',
            'EDITOR', 'VISUAL', 'PAGER', 'BROWSER',
            'PYTHON_PATH', 'NODE_PATH', 'GOPATH', 'JAVA_HOME',
            'DOCKER_HOST', 'KUBECONFIG',
            'AWS_PROFILE', 'AWS_REGION',
            'GIT_CONFIG_GLOBAL'
        ]

        env_vars = {}
        for var in relevant_vars:
            value = os.getenv(var)
            if value:
                env_vars[var] = value

        return env_vars

    def get_current_directory_info(self) -> Dict[str, any]:
        """Get information about the current directory."""
        cwd = os.getcwd()
        info = {
            'path': cwd,
            'is_git_repo': False,
            'git_branch': None,
            'has_package_json': False,
            'has_requirements_txt': False,
            'has_dockerfile': False,
            'has_makefile': False,
            'file_count': 0,
            'dir_count': 0
        }

        try:
            # Check if it's a git repository
            result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                                    capture_output=True, text=True, cwd=cwd)
            if result.returncode == 0:
                info['is_git_repo'] = True

                # Get current branch
                branch_result = subprocess.run(['git', 'branch', '--show-current'],
                                               capture_output=True, text=True, cwd=cwd)
                if branch_result.returncode == 0:
                    info['git_branch'] = branch_result.stdout.strip()
        except FileNotFoundError:
            pass

        # Check for common project files
        common_files = {
            'package.json': 'has_package_json',
            'requirements.txt': 'has_requirements_txt',
            'Dockerfile': 'has_dockerfile',
            'Makefile': 'has_makefile',
            'makefile': 'has_makefile'
        }

        for filename, key in common_files.items():
            if os.path.exists(os.path.join(cwd, filename)):
                info[key] = True

        # Count files and directories
        try:
            entries = os.listdir(cwd)
            for entry in entries:
                path = os.path.join(cwd, entry)
                if os.path.isfile(path):
                    info['file_count'] += 1
                elif os.path.isdir(path):
                    info['dir_count'] += 1
        except PermissionError:
            pass

        return info

    def get_system_resources(self) -> Dict[str, any]:
        """Get basic system resource information."""
        resources = {}

        try:
            # Disk usage of current directory
            result = subprocess.run(
                ['df', '-h', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        resources['disk_usage'] = {
                            'total': parts[1],
                            'used': parts[2],
                            'available': parts[3],
                            'usage_percent': parts[4]
                        }
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        try:
            # Memory usage (Linux/macOS)
            if platform.system() == 'Linux':
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total_kb = int(line.split()[1])
                            resources['memory_total'] = f"{total_kb // 1024}MB"
                        elif line.startswith('MemAvailable:'):
                            available_kb = int(line.split()[1])
                            resources['memory_available'] = f"{available_kb // 1024}MB"

            elif platform.system() == 'Darwin':
                result = subprocess.run(
                    ['vm_stat'], capture_output=True, text=True)
                if result.returncode == 0:
                    resources['memory_info'] = 'Available via vm_stat'

        except (FileNotFoundError, subprocess.CalledProcessError, PermissionError):
            pass

        return resources

    def get_network_info(self) -> Dict[str, any]:
        """Get basic network information."""
        network_info = {}

        try:
            # Check internet connectivity
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'],
                                    capture_output=True, text=True, timeout=5)
            network_info['internet_connected'] = result.returncode == 0
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            network_info['internet_connected'] = False

        try:
            # Get local IP (works on most Unix systems)
            result = subprocess.run(
                ['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                if ips:
                    network_info['local_ip'] = ips[0]
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        return network_info

    def get_full_context(self) -> Dict[str, any]:
        """Get comprehensive system context."""
        return {
            'os': self.get_os_info(),
            'shell': self.get_shell_info(),
            'available_tools': self.get_available_tools(),
            'recent_commands': self.get_recent_commands(),
            'environment': self.get_environment_variables(),
            'current_directory': self.get_current_directory_info(),
            'system_resources': self.get_system_resources(),
            'network': self.get_network_info()
        }

    def clear_cache(self):
        """Clear cached information."""
        self._cached_info.clear()
