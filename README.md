# Ansible Deployment Interactive Script

This repository contains a Python-based interactive wrapper to easily and consistently run Ansible deploy playbooks using Docker. It prompts you for configuration variables like migrations and playbook options, making deployments safer and easier.

---

## Files Overview

### `main.py`
The main entrypoint. It provides a terminal-based interactive UI for running `ansible-playbook` inside a Docker container.

**Key Features:**
*   **Playbook Directory Selection**: Prompts you for the directory containing your project's playbooks before execution, allowing flexibility in your project layout.
*   **Config Directory Selection**: Prompts for the directory containing `ansible.cfg` and SSH keys, with environment variable support (`ANSIBLE_CONFIG_DIR`).
*   **Playbook Selection**: Displays a clear menu of available deploy targets (Frontend/Backend, Prod/Staging).
*   **Docker-based Execution**: Runs `ansible-playbook` inside a Docker container (`mahmoudhesham1350/ansible-playbook:latest`), eliminating the need for local Ansible installation.
*   **Volume Mounting**: Automatically mounts playbooks and config directories into the container.
*   **Vault Password Support**: Passes `--ask-vault-pass` to the container when required by the selected playbook.
*   **Error Handling**: Catches keyboard interrupts seamlessly and exits safely without huge tracebacks.

### `playbooks.py`
This module defines the actual playbooks supported by the script using an extensible Object-Oriented approach. Adding a new playbook is as simple as creating a new class.

**Key Features:**
*   **`Playbook` Base Class**: All playbooks inherit from this. It standardizes attributes like `name`, `file` (the YML file), and whether a vault password is required (`requires_vault_password`).
*   **Interactive & Non-Interactive Modes**: The `get_options()` method supports both interactive prompts and environment variable configuration for CI/CD pipelines.
*   **Backend-Specific Options**: `BackendPlaybook` subclasses prompt the user for whether to run Django migrations (`run_migrations`) or collect static files (`collectstatic`), with support for non-interactive mode via `RUN_MIGRATIONS` and `COLLECTSTATIC` environment variables.
*   **JSON Extra Vars**: Converts options into properly typed JSON extra vars passed to `ansible-playbook`, ensuring boolean values are correctly interpreted.

---

## Requirements

* Docker (must be installed and running)
* Python 3.x (for running the interactive script)

## Usage

### Interactive Mode

The script runs interactively by default, prompting you for playbook directory, config directory, and playbook-specific options:

```bash
python main.py
```

**What it does:**
1. Prompts for playbooks directory (default: `playbooks`)
2. Prompts for config directory containing `ansible.cfg` and SSH keys (default: `playbooks/config`)
3. Shows menu of available playbooks
4. Prompts for playbook-specific options (e.g., migrations, collectstatic)
5. Runs the selected playbook inside a Docker container with the appropriate volumes mounted

**Example Session:**
```
Enter path to the playbooks directory (default: playbooks): 
Enter path to config directory with ansible.cfg and SSH keys (default: playbooks/config): 
==================================================
 Interactive Ansible Deployment Script
==================================================

Available Ansible Playbooks:
  1. Backend Production Deployment
  2. Backend Staging Deployment
  3. Frontend Production Deployment
  4. Frontend Staging Deployment

Select a playbook to run (1-4): 1

Backend specific options:
  Should I run migrations? (y/N): y
  Should I collect static files? (y/N): n

==================================================
Running 'Backend Production Deployment'...
Command: docker run --rm -it -v /path/to/playbooks:/ansible -v /path/to/config:/ansible/config:ro -w /ansible -e ANSIBLE_CONFIG=/ansible/config/ansible.cfg mahmoudhesham1350/ansible-playbook:latest backend.prod.yml --ask-vault-pass -e {"run_migrations": true, "collectstatic": false}
==================================================
```

### Non-Interactive Mode

For CI/CD pipelines or automated deployments, you can use environment variables to skip interactive prompts:

**Environment Variables:**
- `PLAYBOOKS_DIR`: Directory containing playbooks (default: `playbooks`)
- `ANSIBLE_CONFIG_DIR`: Directory containing `ansible.cfg` and SSH keys (default: `playbooks/config`)
- `RUN_MIGRATIONS`: Run database migrations (true/false) - Backend playbooks only
- `COLLECTSTATIC`: Collect static files (true/false) - Backend playbooks only

**Example:**
```bash
PLAYBOOKS_DIR=playbooks \
ANSIBLE_CONFIG_DIR=playbooks/config \
RUN_MIGRATIONS=true \
COLLECTSTATIC=false \
python main.py < <(echo "1")
```

### Docker Image

The project includes a Dockerfile that builds the `ansible-playbook` Docker image used by `main.py`. The image contains:
- Python 3.14
- ansible-core
- Common Ansible collections (community.docker, community.general)
- SSH client and sshpass

**Build the Docker image:**

```bash
docker build -t mahmoudhesham1350/ansible-playbook:latest .
```

**Note:** You typically don't need to build this yourself, as `main.py` uses the pre-built image from Docker Hub.

### Adding a new Playbook

If you want to add a fresh playbook to the menu, add it to `playbooks.py`:

```python
import json

class DatabasePlaybook(Playbook):
    name = "Database Initialization"
    file = "db_init.yml"
    requires_vault_password = True

    def get_options(self) -> dict:
        import sys
        import os
        
        # Support non-interactive mode via environment variables
        if not sys.stdin.isatty():
            reset_db = os.getenv("RESET_DB", "false").lower() in ['true', 'yes', '1', 'y']
            return {"reset_db": reset_db}
        
        # Interactive mode
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
        BackendProdPlaybook(),
        BackendStagingPlaybook(),
        FrontendProdPlaybook(),
        FrontendStagingPlaybook(),
        DatabasePlaybook(),  # Your new playbook added here
    ]
```

---

## Key Changes from Previous Version

**Docker-based Execution**: The script now runs `ansible-playbook` inside a Docker container instead of relying on local Ansible installations or uv. This provides consistent execution environments and eliminates dependency management issues.

**Config Directory Support**: Added support for a separate config directory containing `ansible.cfg` and SSH keys, which gets mounted read-only into the Docker container.

**Non-Interactive Mode**: `playbooks.py` now detects when running in non-interactive mode (via `sys.stdin.isatty()`) and reads configuration from environment variables, making it suitable for CI/CD pipelines.

**No More uv Dependencies**: All Python dependencies are now handled by Docker. You only need Docker installed to run deployments.
