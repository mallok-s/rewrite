"""Test file that uses module-style imports."""

import test_fields


def check_schema():
    """Check schema name."""
    if test_fields.schema_name() == "user_schema":
        print("Schema matches")
    path = test_fields.table_path()
    retries = test_fields.max_retries()
    return (path, retries)
