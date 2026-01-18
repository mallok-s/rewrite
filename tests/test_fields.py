"""Test file with field definitions."""


def schema_name():
    return "user_schema"


def table_path():
    return "/data/tables/users"


def max_retries():
    return 3


default_val = backup_val = "test"
CONSTANT_VALUE = 100
_private_field = "private"
