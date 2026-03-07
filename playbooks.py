class Playbook:
    name = ""
    file = ""
    requires_vault_password = False

    def get_options(self) -> dict:
        """Override this to ask for playbook-specific options."""
        return {}

    def get_extra_vars(self, options: dict) -> list[str]:
        """Override this to convert options into ansible extra vars (-e)."""
        return []

class BackendPlaybook(Playbook):
    def get_options(self) -> dict:
        print("\nBackend specific options:")
        run_migrations = input("  Should I run migrations? (y/N): ").strip().lower() in ['y', 'yes']
        collectstatic = input("  Should I collect static files? (y/N): ").strip().lower() in ['y', 'yes']
        return {
            "run_migrations": run_migrations,
            "collectstatic": collectstatic,
        }

    def get_extra_vars(self, options: dict) -> list[str]:
        # Passing extra-vars as a JSON string ensures Ansible parses the values as actual booleans, 
        # avoiding the "Conditional result was derived from value of type 'str'..." error.
        import json
        extra_vars = {
            "run_migrations": bool(options.get('run_migrations')),
            "collectstatic": bool(options.get('collectstatic')),
        }
        return ["-e", json.dumps(extra_vars)]

class BackendProdPlaybook(BackendPlaybook):
    name = "Backend Production Deployment"
    file = "backend.prod.yml"
    requires_vault_password = True

class BackendStagingPlaybook(BackendPlaybook):
    name = "Backend Staging Deployment"
    file = "backend.staging.yml"
    requires_vault_password = True


class FrontendProdPlaybook(Playbook):
    name = "Frontend Production Deployment"
    file = "frontend.prod.yml"
    requires_vault_password = True

class FrontendStagingPlaybook(Playbook):
    name = "Frontend Staging Deployment"
    file = "frontend.staging.yml"
    requires_vault_password = True
