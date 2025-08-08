import typer
import click
import platform
import subprocess
import sys
import os

app = typer.Typer(help="lltools: A collection of useful CLI tools.")


@app.command()
def update():
    """update package"""
    repo_url = "git+https://github.com/lolikonloli/lltools.git"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", repo_url])


@app.command()
def init():
    """Initialize shell completion for lltools (Linux/macOS/Windows) without duplication."""
    os_type = platform.system()

    def append_if_missing(file_path: str, content: str, marker: str):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                existing = f.read()
            if marker in existing:
                typer.echo(f"[Skip] Completion already present in {file_path}")
                return
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n# {marker}\n{content}\n")
        typer.echo(f"[Added] Completion written to {file_path}")

    try:
        shell = os.environ.get("SHELL") or os.environ.get("ComSpec") or ""
        shell_name = os.path.basename(shell).lower()
        typer.echo(f"Detected OS: {os_type}, Shell: {shell_name}")

        if os_type in ["Linux", "Darwin"]:
            if "zsh" in shell_name:
                rc_file = os.path.expanduser("~/.zshrc")
                shell_type = "zsh"
            elif "bash" in shell_name:
                rc_file = os.path.expanduser("~/.bashrc")
                shell_type = "bash"
            else:
                typer.echo("Unsupported shell. Use lltools --install-completion manually.")
                return

            script = subprocess.check_output(["lltools", "--show-completion", shell_type], text=True)
            append_if_missing(rc_file, script, "lltools completion")
            typer.echo(f"Run: source {rc_file} to enable completion")

        elif os_type == "Windows":
            profile = os.path.join(os.environ["USERPROFILE"], "Documents", "WindowsPowerShell",
                                   "Microsoft.PowerShell_profile.ps1")
            script = subprocess.check_output(["lltools", "--show-completion", "powershell"], text=True)
            append_if_missing(profile, script, "lltools completion")
            typer.echo(f"Restart PowerShell or run: . '{profile}'")

        else:
            typer.echo("Unsupported OS. Use lltools --install-completion manually.")

    except Exception as e:
        typer.echo(f"Error initializing completion: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
