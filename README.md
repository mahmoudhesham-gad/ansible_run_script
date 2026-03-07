# Ansible Deployment Interactive Script

This repository contains a Python-based interactive wrapper to easily and consistently run Ansible deploy playbooks. It prompts you for configuration variables like migrations, vault passwords, and host inventories, making deployments safer and easier.

---

## Files Overview

### `main.py`
The main entrypoint. It provides a terminal-based interactive UI for running `ansible-playbook`. 

**Key Features:**
*   **Playbook Directory Selection**: Prompts you for the directory containing your project's playbooks before execution, allowing flexibility in your project layout.
*   **Playbook Selection**: Displays a clear menu of available deploy targets (Frontend/Backend, Prod/Staging).
*   **Automatic Runner Detection**: Looks for the `ansible-playbook` command locally, and gracefully falls back to `uv run ansible-playbook` if Ansible is managed within `uv`.
*   **Vault Password Auto-detection**: Automatically looks for a `.ansible_password` file. If missing (and required by the selected playbook), it prompts you to provide a custom file path.
*   **Hosts File Auto-detection**: Defaults to using the local `hosts.ini` file. If not found, it asks you to supply a path to a valid hosts file.
*   **Error Handling**: Catches keyboard interrupts seamlessly and exits safely without huge tracebacks.

### `playbooks.py`
This module defines the actual playbooks supported by the script using an extensible Object-Oriented approach. Adding a new playbook is as simple as creating a new class.

**Key Features:**
*   **`Playbook` Base Class**: All playbooks inherit from this. It standardizes attributes like `name`, `file` (the YML file), and whether a vault password is required (`requires_vault_password`).
*   **Interactive Options Prompts**: Through the `get_options()` and `get_extra_vars()` methods, different types of playbooks can prompt for their own specific configurations.
    *   *For example*, `BackendPlaybook` subclasses prompt the user for whether to run Django migrations (`run_migrations`) or collect static files (`collectstatic`). It translates these Yes/No inputs into `-e run_migrations=true/false` arguments passed to `ansible-playbook`.

---

## Requirements

* Python 3.14
* `ansible` (must be installed globally or have uv installed)

## Usage

You can run the interactive prompt using straight Python:

```bash
python main.py
```

Or using `uv` if managing dependencies closely:

```bash
uv run main.py
```

### Adding a new Playbook

If you want to add a fresh playbook to the menu, add it to `playbooks.py`:

```python
import json

class DatabasePlaybook(Playbook):
    name = "Database Initialization"
    file = "db_init.yml"
    requires_vault_password = True

    def get_options(self) -> dict:
        reset_db = input("Should I drop and reset the DB? (y/N): ").strip().lower() in ['y', 'yes']
        return {"reset_db": reset_db}

    def get_extra_vars(self, options: dict) -> list[str]:
        # Passing extra-vars as a JSON string ensures Ansible parses the values as actual booleans
        extra_vars = {
            "reset_db": bool(options.get('reset_db'))
        }
        return ["-e", json.dumps(extra_vars)]
```

Then append your new class to the `PLAYBOOKS` list inside the `AnsibleInteractive` class in `main.py`:

```python
    PLAYBOOKS = [
        DatabasePlaybook(), # Your Playbooks added here
    ]
```
