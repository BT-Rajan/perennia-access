# perennia-access

Compact authorization core for Perennia apps. Backend-only, MySQL-backed role-based access control. Requires `perennia-auth` for authenticated identity.

## Install

In a consuming app's `requirements.txt`:

```
git+https://github.com/BT-Rajan/perennia-access.git@v1.0.0
```

`perennia-auth` is a required dependency and will be installed automatically.

## Schema

Run `perennia_access/schema.sql` against your MySQL database once.

## Organizational Rules

`perennia-access` is backend authorization only.

### Required Dependency on `perennia-auth`

`perennia-access` cannot function without `perennia-auth`. It uses the authenticated identity model from `perennia-auth`.

```
perennia-auth
    ↓
Authenticated Identity
    ↓
perennia-access
    ↓
Authorization Decision
```

### Backend Only

No frontend code. No HTML, CSS, JavaScript, Vue, React, or UI rendering.

The application decides how authorization affects the frontend.

The backend remains the security boundary.

### No Silent Failures

Every authorization operation produces a clear error. Infrastructure failures are distinguished from authorization denials.

### Error Handling

Three classes of failure:

- **`AuthorizationDenied`**: User is authenticated but lacks the permission.
- **`PermissionNotFoundError`** or **`RoleNotFoundError`**: Configuration/data error.
- **`AccessDatabaseError`**: Infrastructure failure (database unavailable, etc.).

The application must distinguish these cases.

## Usage

### Setup

```python
from perennia_auth import PerenniaAuth, AuthConfig, DatabaseConfig as AuthDatabaseConfig
from perennia_access import PerenniaAccess, AccessConfig, DatabaseConfig, AuthenticatedIdentity

# Perennia Auth
auth_config = AuthConfig(
    signing_secret="replace-with-a-long-random-secret",
    database=AuthDatabaseConfig(host="localhost", user="app", password="...", database="app_db"),
)
auth = PerenniaAuth(auth_config, mailer=YourMailer())

# Perennia Access
access_config = AccessConfig(
    database=DatabaseConfig(host="localhost", user="app", password="...", database="app_db"),
)
access = PerenniaAccess(access_config)
```

### Create Permissions and Roles

Permissions and roles are application-defined.

```python
# Create permissions
access.create_permission("customer.view", "View customer details")
access.create_permission("customer.edit", "Edit customer details")
access.create_permission("invoice.approve", "Approve invoices")

# Create roles
access.create_role("viewer", "Can view resources")
access.create_role("editor", "Can view and edit resources")
access.create_role("accountant", "Can manage invoices")

# Assign permissions to roles
access.assign_permission_to_role("viewer", "customer.view")
access.assign_permission_to_role("editor", "customer.view")
access.assign_permission_to_role("editor", "customer.edit")
access.assign_permission_to_role("accountant", "invoice.approve")
```

### Authenticate and Authorize

```python
# User logs in
auth_result = auth.authenticate("user@example.com", "password")
claims = auth.verify_access_token(auth_result.access_token)

# Create authenticated identity for use with perennia-access
# The identity comes from perennia-auth verification
identity = AuthenticatedIdentity(
    subject_id=claims["sub"],
    session_id=claims["sid"],
)

# Assign role to user
access.assign_role_to_user(identity.subject_id, "viewer")

# Check authorization
if access.can(identity, "customer.view"):
    # User can view customers
    show_customers()

# Require authorization (raises if denied)
try:
    access.require(identity, "customer.edit")
    edit_customer(customer_id)
except AuthorizationDenied:
    return error_response("You do not have permission to edit customers")

# Get user's permissions
permissions = access.get_identity_permissions(identity)
# ['customer.view']

# Get user's roles
roles = access.get_identity_roles(identity)
# ['viewer']
```

## Public API

### Authorization Checks

**`can(identity: AuthenticatedIdentity, permission_code: str) -> bool`**

Check if an identity has a permission. Returns `True` or `False`.

Raises:
- `InvalidIdentityError`: Identity is invalid
- `PermissionNotFoundError`: Permission does not exist
- `AccessDatabaseError`: Database query failed

**`require(identity: AuthenticatedIdentity, permission_code: str) -> None`**

Require a permission or raise `AuthorizationDenied`.

Raises:
- `InvalidIdentityError`: Identity is invalid
- `PermissionNotFoundError`: Permission does not exist
- `AuthorizationDenied`: Identity lacks permission
- `AccessDatabaseError`: Database query failed

**`get_identity_permissions(identity: AuthenticatedIdentity) -> List[str]`**

Get all permission codes for an identity.

**`get_identity_roles(identity: AuthenticatedIdentity) -> List[str]`**

Get all role codes for an identity.

### Permission Management

**`create_permission(code: str, description: str) -> Permission`**

Create a new permission.

**`get_permission(code: str) -> Optional[Permission]`**

Get a permission by code.

**`list_permissions() -> List[Permission]`**

List all permissions.

### Role Management

**`create_role(code: str, description: str) -> Role`**

Create a new role.

**`get_role(code: str) -> Optional[Role]`**

Get a role by code.

**`list_roles() -> List[Role]`**

List all roles.

### Role-Permission Assignment

**`assign_permission_to_role(role_code: str, permission_code: str) -> None`**

Assign a permission to a role.

Raises:
- `RoleNotFoundError`: Role does not exist
- `PermissionNotFoundError`: Permission does not exist

**`unassign_permission_from_role(role_code: str, permission_code: str) -> bool`**

Unassign a permission from a role. Returns `True` if removed, `False` if not found.

**`get_role_permissions(role_code: str) -> List[str]`**

Get all permission codes for a role.

### User-Role Assignment

**`assign_role_to_user(subject_id: str, role_code: str) -> None`**

Assign a role to a user (subject).

Raises:
- `RoleNotFoundError`: Role does not exist

**`unassign_role_from_user(subject_id: str, role_code: str) -> bool`**

Unassign a role from a user (subject). Returns `True` if removed, `False` if not found.

## Architecture

```
┌────────────────────────────────────────────┐
│              APPLICATION                   │
│                                            │
│  Business logic, API routes, frontend      │
│  Defines and uses application permissions  │
└─────────────────────┬──────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│           perennia-access                  │
│                                            │
│  Requires perennia-auth                    │
│  Roles → Permissions → Authorization       │
└─────────────────────┬──────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│            perennia-auth                   │
│                                            │
│  Authentication, sessions, tokens          │
└────────────────────────────────────────────┘
```

## Error Handling

Always distinguish between authorization denial and infrastructure failure.

```python
try:
    access.require(identity, "invoice.approve")
    process_invoice()
except AuthorizationDenied:
    # User is authenticated but lacks permission
    return {"error": "You do not have permission to approve invoices"}
except AccessDatabaseError:
    # Database is down
    return {"error": "Service unavailable"}
except Exception as e:
    # Unexpected error
    log_error(e)
    return {"error": "Unexpected error"}
```

## No Frontend Authorization

Frontend behavior may improve user experience, but it is never security.

Always authorize on the backend:

```python
# Backend: verify authorization regardless of frontend state
try:
    access.require(identity, "customer.edit")
    return update_customer(customer_data)
except AuthorizationDenied:
    return {"error": "Unauthorized"}
```

Frontend can use `get_identity_permissions()` to decide what to show, but the backend must independently verify every protected operation.

## License

Same as perennia-auth.
