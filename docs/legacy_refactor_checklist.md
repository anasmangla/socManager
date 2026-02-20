# Legacy Page Migration / Refactor Checklist

Use this quick pass when upgrading legacy pages:

1. Replace deprecated database calls with ORM/PDO-equivalent prepared queries.
2. Enforce authentication/authorization (`require_login()` equivalent) on protected routes.
3. Escape all user-provided output before rendering in HTML/JS.
4. Validate and sanitize all incoming request fields.
5. Verify search behavior and large-list pagination still work.
6. Verify print rendering behavior and no warning output in logs/responses.
