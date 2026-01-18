"""Module scanner to find Python files in the same module."""

import subprocess
from pathlib import Path


def find_git_root(path):
    """
    Find the git repository root.

    Args:
        path: Path to start searching from

    Returns:
        Path or None: Git root directory or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def find_module_root(target_file):
    """
    Find the root directory of the Python module containing target_file.

    The module root is determined by walking up the directory tree until:
    1. We find a parent directory without __init__.py, or
    2. We reach the git repository root, or
    3. We reach the filesystem root

    Args:
        target_file: Path to the target Python file

    Returns:
        Path: The module root directory
    """
    target_path = Path(target_file).resolve()
    current_dir = target_path.parent

    # Find git root as a potential boundary
    git_root = find_git_root(current_dir)

    # Start from the target file's directory and walk up
    module_root = current_dir

    while True:
        parent = current_dir.parent

        # Stop if we've reached the filesystem root
        if parent == current_dir:
            break

        # Stop if we've reached the git root
        if git_root and current_dir == git_root:
            break

        # Check if parent has __init__.py
        if not (parent / "__init__.py").exists():
            # Parent is not a Python package, so current_dir is the module root
            break

        # Move up one level
        module_root = current_dir
        current_dir = parent

    return module_root


def find_python_files(module_root, exclude_dirs=None):
    """
    Recursively find all Python files in the module.

    Args:
        module_root: Root directory of the module
        exclude_dirs: Set of directory names to exclude (e.g., {'__pycache__', '.git'})

    Returns:
        list: List of Path objects for Python files
    """
    if exclude_dirs is None:
        exclude_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache"}

    python_files = []

    for path in Path(module_root).rglob("*.py"):
        # Skip if any parent directory is in exclude_dirs
        if any(parent.name in exclude_dirs for parent in path.parents):
            continue

        python_files.append(path)

    return python_files


def scan_module(target_file):
    """
    Scan the module containing target_file and return all Python files.

    Args:
        target_file: Path to the target Python file

    Returns:
        tuple: (module_root Path, list of Python file Paths)
    """
    module_root = find_module_root(target_file)
    python_files = find_python_files(module_root)

    return module_root, python_files
