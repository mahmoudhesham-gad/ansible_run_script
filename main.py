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
    _PLAYBOOKS_DIR: str = "playbooks"
    _CONFIG_DIR: str = "config"
    _OPTIONS: dict = {}
    _SELECTED_PLAYBOOK: Playbook
    _DOCKER_IMAGE: str = "mahmoudhesham1350/ansible-playbook:latest"

    def __init__(self):
        default_playbooks_dir = os.getenv("PLAYBOOKS_DIR", self._PLAYBOOKS_DIR)
        dir_path = input(f"Enter path to the playbooks directory (default: {default_playbooks_dir}): ").strip()
        if not dir_path:
            dir_path = default_playbooks_dir
        if not os.path.exists(dir_path):
            raise ValueError(f"The directory '{dir_path}' was not found.")
        self._PLAYBOOKS_DIR = os.path.abspath(dir_path)

        default_config = os.getenv("ANSIBLE_CONFIG_DIR", os.path.join(dir_path, self._CONFIG_DIR))
        config_dir = input(f"Enter path to config directory with ansible.cfg and SSH keys (default: {default_config}): ").strip()
        if not config_dir:
            config_dir = default_config
        if not os.path.exists(config_dir):
            raise ValueError(f"The config directory '{config_dir}' was not found.")
        self._CONFIG_DIR = os.path.abspath(config_dir)

    def _set_playbook(self):
        selection = input(f"\nSelect a playbook to run (1-{len(self.PLAYBOOKS)}): ").strip()
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(self.PLAYBOOKS):
                self._SELECTED_PLAYBOOK = self.PLAYBOOKS[idx]
            else:
                raise ValueError("Selection out of range.")
        except (ValueError, IndexError):
            raise ValueError("Invalid selection. Please choose a valid playbook number.")

    def _set_options(self):
        if not self._SELECTED_PLAYBOOK:
            raise ValueError("No playbook selected.")
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

    def get_cmd(self) -> list[str]:
        playbook: Playbook = self._SELECTED_PLAYBOOK
        cmd =  [
            "docker", "run", "--rm", "-it",
            "-v", f"{self._PLAYBOOKS_DIR}:/ansible",
            "-v", f"{self._CONFIG_DIR}:/ansible/config:ro",
            "-w", "/ansible",
            "-e", "ANSIBLE_CONFIG=/ansible/config/ansible.cfg",
            self._DOCKER_IMAGE,
            playbook.file,
        ]
        if playbook.requires_vault_password:
            cmd.append("--ask-vault-pass")

        cmd.extend(playbook.get_extra_vars(self._OPTIONS))
        return cmd

    def run_playbook(self):
        if not shutil.which("docker"):
            print("Error: 'docker' command not found. Please install Docker Desktop.", file=sys.stderr)
            sys.exit(1)

        cmd = self.get_cmd()

        print("\n" + "=" * 50)
        print(f"Running '{self._SELECTED_PLAYBOOK.name}'...")
        print(f"Command: {' '.join(cmd)}")
        print("=" * 50 + "\n")

        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                print("\nDeployment completed successfully!")
            else:
                print(f"\nAnsible playbook failed with exit code {result.returncode}", file=sys.stderr)
                sys.exit(result.returncode)
        except FileNotFoundError:
            print("Error: Could not execute docker.", file=sys.stderr)
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
