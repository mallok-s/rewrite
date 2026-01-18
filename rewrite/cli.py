"""Main CLI entry point for the rewrite tool."""

import argparse
import sys
from pathlib import Path

from rewrite.analyzer import analyze_file
from rewrite.config import get_glob_pattern, validate_pattern
from rewrite.output import OutputFormatter, format_function_preview
from rewrite.scanner import scan_module
from rewrite.transformer import transform_file
from rewrite.usage_updater import update_usage_file


def cli():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Convert Python variables to functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rewrite path/to/my_fields.py              # Dry-run with saved pattern
  rewrite path/to/my_fields.py --apply      # Apply changes
  rewrite path/to/file.py --pattern "*.py"  # Override pattern
        """,
    )
    parser.add_argument("target_file", help="Path to the Python file to convert")
    parser.add_argument(
        "--pattern", help="Glob pattern for filename validation (overrides saved pattern)"
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")

    args = parser.parse_args()

    # Validate target file exists
    target_file = Path(args.target_file)
    if not target_file.exists():
        print(f"ERROR: File not found: {target_file}")
        sys.exit(1)

    if not target_file.is_file():
        print(f"ERROR: Not a file: {target_file}")
        sys.exit(1)

    # Get and validate pattern
    pattern = get_glob_pattern(args.pattern)
    filename = target_file.name

    formatter = OutputFormatter()
    matches = validate_pattern(filename, pattern)
    formatter.print_pattern_check(filename, pattern, matches)

    if not matches:
        sys.exit(1)

    try:
        # Step 1: Analyze the target file
        variables, skipped = analyze_file(target_file)

        if not variables and not skipped:
            print(f"\nNo lowercase_snake_case variables found in {target_file}")
            sys.exit(0)

        # Step 2: Print what we found
        formatter.print_conversion_header(target_file)

        for var in variables:
            preview = format_function_preview(var)
            formatter.print_variable_conversion(var, preview)

        for skip in skipped:
            formatter.print_skipped(skip)

        # Step 3: Scan the module for other files
        module_root, python_files = scan_module(target_file)

        # Create set of converted variable names
        var_names = {var.name for var in variables}

        # Step 4: Analyze and update usage sites
        files_to_update = {}
        star_warnings = []

        formatter.print_usage_header()

        for py_file in python_files:
            # Skip the target file itself
            if py_file.resolve() == target_file.resolve():
                continue

            new_source, updates, warnings = update_usage_file(
                py_file, target_file, module_root, var_names
            )

            if new_source:
                files_to_update[py_file] = new_source

            if updates:
                formatter.print_file_updates(py_file, updates)

            if warnings:
                for warning in warnings:
                    formatter.print_star_import_warning(py_file, warning)
                    star_warnings.extend(warnings)

        # Step 5: Apply changes or print summary
        if args.apply:
            # Transform the target file
            transformed_source = transform_file(target_file, variables)

            # Write the target file
            with open(target_file, "w") as f:
                f.write(transformed_source)

            # Write updated usage files
            for file_path, new_source in files_to_update.items():
                with open(file_path, "w") as f:
                    f.write(new_source)

            formatter.print_summary(dry_run=False)
            formatter.print_apply_confirmation()
        else:
            formatter.print_summary(dry_run=True)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
