import os
import sys
import shutil
import subprocess
from playbooks import (
    Playbook,
    BackendProdPlaybook,
    BackendStagingPlaybook,
    FrontendProdPlaybook,
    FrontendStagingPlaybook,
)

class AnsibleInteractive:
    PLAYBOOKS = [
        BackendProdPlaybook(),
        BackendStagingPlaybook(),
        FrontendProdPlaybook(),
        FrontendStagingPlaybook(),
    ]
    _VAULT_PASSWORD_FILE: str = ".ansible_password"
    _HOSTS_FILE: str = "hosts.ini"
    _OPTIONS: dict = {}
    _SELECTED_PLAYBOOK: Playbook 

    def __init__(self):
        self.DIR = input("Enter path to the playbooks directory (default: .): ").strip() or ""
        if not os.path.exists(self.DIR):
            raise ValueError(f"The playbooks directory '{self.DIR}' was not found.")
        os.chdir(self.DIR)

    def _set_vault_password_file(self):
        if not os.path.exists(self._VAULT_PASSWORD_FILE):
            print(f"\nWarning: The default vault password file '{self._VAULT_PASSWORD_FILE}' was not found.")
            vault_password_file = input("Enter path to the vault password file: ").strip()
            if not os.path.exists(vault_password_file):
                raise ValueError(f"The vault password file '{vault_password_file}' was not found either.")
        else:
            print(f"Using default vault password file '{self._VAULT_PASSWORD_FILE}'.")
        self._VAULT_PASSWORD_FILE = vault_password_file


    def _set_hosts_file(self):
        if not os.path.exists(self._HOSTS_FILE):
            print(f"\nWarning: The default hosts file '{self._HOSTS_FILE}' was not found.")
            hosts_file = input("Enter path to the hosts file: ").strip()
            if not os.path.exists(hosts_file):
                raise ValueError(f"The hosts file '{hosts_file}' was not found either.")
            self._HOSTS_FILE = hosts_file
        else:
            print(f"Using default hosts file '{self._HOSTS_FILE}'.")


    def _set_playbook(self):
        selection = input(f"\nSelect a playbook to run (1-{len(self.PLAYBOOKS)}): ").strip()
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(self.PLAYBOOKS):
                self._SELECTED_PLAYBOOK = self.PLAYBOOKS[idx]
        except Exception:
            raise ValueError("Invalid selection. Please choose a valid playbook number.")
    
    def _set_options(self):
        if not self._SELECTED_PLAYBOOK:
            raise ValueError("No playbook selected")
        self._OPTIONS = self._SELECTED_PLAYBOOK.get_options()

    def menu(self) -> None:
        print("=" * 50)
        print(" Interactive Ansible Deployment Script")
        print("=" * 50)
        print("\nAvailable Ansible Playbooks:")
        for idx, playbook in enumerate(self.PLAYBOOKS, 1):
            print(f"  {idx}. {playbook.name}")

        self._set_playbook()
        self._set_options()
        self._set_hosts_file()
        if self._SELECTED_PLAYBOOK.requires_vault_password:
            self._set_vault_password_file()


    def run_playbook(self):
        playbook: Playbook = self._SELECTED_PLAYBOOK
        
        # Determine how to run ansible-playbook
        # First check if ansible-playbook is in PATH (e.g., if running inside uv run or venv)
        cmd_prefix = []
        if shutil.which("ansible-playbook"):
            cmd_prefix = ["ansible-playbook"]
        elif shutil.which("uv"):
            print("Ansible not found in PATH, but 'uv' is present. Will run using 'uv run ansible-playbook'.")
            cmd_prefix = ["uv", "run", "ansible-playbook"]
        else:
            print("Error: 'ansible-playbook' command not found, and 'uv' is not installed.", file=sys.stderr)
            print("Please install ansible, or run this script via 'uv run main.py'.", file=sys.stderr)
            sys.exit(1)

        cmd = cmd_prefix + ["-i", self._HOSTS_FILE, playbook.file]

        if self._VAULT_PASSWORD_FILE:
            cmd.extend(["--vault-password-file", self._VAULT_PASSWORD_FILE])

        cmd.extend(playbook.get_extra_vars(self._OPTIONS))

        print("\n" + "=" * 50)
        print(f"Running '{playbook.name}'...")
        print(f"Command: {' '.join(cmd)}")
        print("=" * 50 + "\n")

        try:
            # We don't use check=True because we want to handle the error our way without a python traceback
            result = subprocess.run(cmd)
            if result.returncode == 0:
                print("\nDeployment completed successfully!")
            else:
                print(f"\nAnsible playbook failed with exit code {result.returncode}", file=sys.stderr)
                sys.exit(result.returncode)
        except FileNotFoundError:
            print("Error: Could not execute ansible-playbook.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nPlaybook execution cancelled by user.")
            sys.exit(1)

def main():
    try:
        ansible_interactive = AnsibleInteractive()
        ansible_interactive.menu()
        ansible_interactive.run_playbook()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
