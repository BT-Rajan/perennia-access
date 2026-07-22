"""Test configuration and fixtures."""

import pytest
import pymysql
from perennia_access import PerenniaAccess, AccessConfig, DatabaseConfig, AuthenticatedIdentity


@pytest.fixture
def db_config():
    """Database configuration for tests."""
    return DatabaseConfig(
        host="localhost",
        user="root",
        password="",
        database="perennia_access_test",
    )


@pytest.fixture
def access_config(db_config):
    """Access configuration for tests."""
    return AccessConfig(database=db_config)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(db_config):
    """Set up the test database and schema."""
    try:
        # Create test database
        conn = pymysql.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
        )
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {db_config.database}")
        cursor.execute(f"CREATE DATABASE {db_config.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
    except pymysql.Error:
        pytest.skip("Test database setup failed; MySQL may not be running")


@pytest.fixture
def access_instance(access_config):
    """Create a PerenniaAccess instance for testing."""
    access = PerenniaAccess(access_config)
    
    # Load schema
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "..", "perennia_access", "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    for statement in statements:
        try:
            import pymysql.cursors
            conn = pymysql.connect(
                host=access_config.database.host,
                user=access_config.database.user,
                password=access_config.database.password,
                database=access_config.database.database,
                cursorclass=pymysql.cursors.DictCursor,
            )
            cursor = conn.cursor()
            cursor.execute(statement)
            conn.commit()
            cursor.close()
            conn.close()
        except pymysql.Error:
            pass
    
    yield access


@pytest.fixture
def sample_identity():
    """Sample authenticated identity for testing."""
    return AuthenticatedIdentity(
        subject_id="user-1",
        session_id="session-1",
    )


@pytest.fixture
def setup_sample_data(access_instance):
    """Set up sample permissions, roles, and assignments."""
    # Create permissions
    access_instance.create_permission("customer.view", "View customer details")
    access_instance.create_permission("customer.edit", "Edit customer details")
    access_instance.create_permission("invoice.view", "View invoices")
    access_instance.create_permission("invoice.approve", "Approve invoices")
    
    # Create roles
    access_instance.create_role("viewer", "Can view resources")
    access_instance.create_role("editor", "Can view and edit resources")
    access_instance.create_role("accountant", "Can manage invoices")
    
    # Assign permissions to roles
    access_instance.assign_permission_to_role("viewer", "customer.view")
    access_instance.assign_permission_to_role("viewer", "invoice.view")
    access_instance.assign_permission_to_role("editor", "customer.view")
    access_instance.assign_permission_to_role("editor", "customer.edit")
    access_instance.assign_permission_to_role("accountant", "invoice.view")
    access_instance.assign_permission_to_role("accountant", "invoice.approve")
    
    return access_instance
