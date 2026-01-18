"""Output formatting for dry-run and apply modes."""


class OutputFormatter:
    """Formats output for the CLI."""

    def __init__(self):
        self.warnings_count = 0
        self.conversions_count = 0
        self.files_updated = set()

    def print_pattern_check(self, filename, pattern, matches):
        """Print pattern validation result."""
        status = "✓" if matches else "✗"
        print(f"\nChecking pattern: {filename} matches {pattern} {status}")
        if not matches:
            print(f"ERROR: File does not match pattern '{pattern}'")

    def print_conversion_header(self, target_file):
        """Print header for variable conversion section."""
        print(f"\nConverting variables in: {target_file}")

    def print_variable_conversion(self, variable, new_code_preview):
        """Print a variable conversion."""
        # Truncate long values for display
        preview = new_code_preview
        if len(preview) > 80:
            preview = preview[:77] + "..."

        print(f"  ✓ {variable.name} (line {variable.lineno})")
        print(f"    {variable.name} = {variable.value_source}")
        print(f"    → {preview}")
        self.conversions_count += 1

    def print_skipped(self, skipped):
        """Print a skipped pattern."""
        source = skipped.source
        if len(source) > 60:
            source = source[:57] + "..."

        print(f"  ⚠ skipped (line {skipped.lineno}): {source}")
        print(f"    Reason: {skipped.reason}")
        self.warnings_count += 1

    def print_usage_header(self):
        """Print header for usage update section."""
        print("\nUpdating usage sites:")

    def print_file_updates(self, file_path, updates):
        """Print updates for a specific file."""
        print(f"  {file_path}")
        for update in updates:
            import_style = f"imported as: from {update.import_info.module_name} import {update.import_info.original_name}"
            if update.import_info.import_type == "direct":
                import_style = f"imported as: import {update.import_info.module_name}"

            print(f"    ✓ line {update.lineno}: {update.original} → {update.updated}")
            print(f"      ({import_style})")

        self.files_updated.add(file_path)

    def print_star_import_warning(self, file_path, warning):
        """Print warning about star import."""
        print(f"  {file_path}")
        print(
            f"    ⚠ line {warning.lineno}: from {warning.module_name} import * (star import - manual review needed)"
        )
        self.warnings_count += 1

    def print_summary(self, dry_run=True):
        """Print summary of changes."""
        print("\nSummary:")
        print(f"  {self.conversions_count} variable(s) converted")
        print(f"  {len(self.files_updated)} file(s) updated")
        if self.warnings_count > 0:
            print(f"  {self.warnings_count} warning(s)")

        if dry_run:
            print("\nRun with --apply to make changes.")

    def print_apply_confirmation(self):
        """Print confirmation after applying changes."""
        print("\n✓ Changes applied successfully!")
        print(f"  Modified {self.conversions_count + len(self.files_updated)} file(s)")


def format_function_preview(variable):
    """
    Format a preview of the function that will be created.

    Args:
        variable: Variable object

    Returns:
        str: Preview of the function definition
    """
    value = variable.value_source
    if len(value) > 50:
        value = value[:47] + "..."

    return f"def {variable.name}(): return {value}"
