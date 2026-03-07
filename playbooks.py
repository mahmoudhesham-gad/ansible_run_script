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
        return [
            "-e", f"run_migrations={'true' if options.get('run_migrations') else 'false'}",
            "-e", f"collectstatic={'true' if options.get('collectstatic') else 'false'}",
        ]

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
