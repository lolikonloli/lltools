import os
import typer
import click
import platform
import subprocess
import sys
import os
from pathlib import Path
import os
import shutil
import subprocess
from pathlib import Path
import requests

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


@app.command()
def gen_ssh_key():
    key_path = Path("~/.ssh/id_rsa").expanduser()
    pubkey_path = Path(str(key_path) + ".pub")

    key_path.parent.mkdir(parents=True, exist_ok=True)

    if key_path.exists() and pubkey_path.exists():
        print(f"SSH key already exists at {key_path}")
        return

    typer.echo("Generating new SSH key...")
    cmd = ["ssh-keygen", "-t", "rsa", "-f", str(key_path), "-b", "4096"]

    subprocess.run(cmd, check=True)

    if os.name == "posix":
        os.chmod(key_path, 0o600)
        os.chmod(pubkey_path, 0o644)

    print(f"SSH key generated at {key_path}")


@app.command()
def upload_ssh_key(ssh_command: str = typer.Option(..., "--ssh_command", help="usr@ip:port"),
                   key_path: Path = typer.Option(Path("~/.ssh/id_rsa.pub").expanduser(), "--key-path", help="私钥路径")) -> None:

    if ":" in ssh_command:
        user_ip, port = ssh_command.split(":")
        user, ip = user_ip.split("@")
    else:
        port = "22"
        user, ip = ssh_command.split("@")

    if not key_path.exists():
        typer.echo("~/.ssh/id_rsa.pub文件不存在，使用lltools gen-ssh-key命令生成秘钥")
        return

    typer.echo(f"目标：{user}@{ip}:{port}")
    try:
        if os.name == "nt":
            key_text = key_path.read_text(encoding="utf-8").strip()
            key_escaped = key_text.replace("'", r"'\''")
            remote_cmd = ("umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; "
                          "chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys; "
                          f"grep -qxF '{key_escaped}' ~/.ssh/authorized_keys || echo '{key_escaped}' >> ~/.ssh/authorized_keys")

            if not shutil.which("ssh"):
                raise RuntimeError("❌ Windows 未找到 ssh，请先启用 OpenSSH Client。")
            subprocess.run(["ssh", f"-p{port}", f"{user}@{ip}", remote_cmd], check=True, timeout=timeout)
        else:
            subprocess.run(["ssh-copy-id", "-i", str(key_path), f"-p{port}", f"{user}@{ip}"], check=True, timeout=120)

        typer.echo("公钥上传完成")
    except subprocess.CalledProcessError as e:
        typer.echo(f"上传失败（退出码 {e.returncode}）")
        raise
    except Exception as e:
        typer.echo(f"上传失败：{e}")
        raise


if __name__ == "__main__":
    app()
