"""Test file that uses fields from test_fields."""

from test_fields import max_retries, schema_name, table_path


def process_data():
    """Process data using imported fields."""
    print(f"Schema: {schema_name()}")
    print(f"Table: {table_path()}")
    for i in range(max_retries()):
        print(f"Attempt {i}")
    return schema_name()


def get_config():
    """Get configuration."""
    return {"schema": schema_name(), "path": table_path(), "retries": max_retries()}
