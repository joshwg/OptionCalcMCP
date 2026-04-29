# Workspace Agent Instructions

- Use WSL2 Ubuntu for all shell and Python work in this repository.
- Do not use PowerShell, Command Prompt, or the Windows `.venv` for repo tasks unless the user explicitly asks for a Windows-specific action.
- Prefer commands in the form `wsl.exe bash -lc "cd /mnt/c/Users/josh/Docs/lab/OptionCalculator && ..."` when invoking a shell from Windows-hosted tooling.
- Treat `venv` as the only supported project environment. Use `venv/bin/python`, `source venv/bin/activate`, and Linux-style paths.
- Do not suggest or restore `.venv`, `Scripts\\python.exe`, `Activate.ps1`, or other PowerShell-specific environment commands in docs, code samples, tests, or config.
- When updating local run commands, prefer `python3` or `venv/bin/python` under WSL.
- Keep Windows-specific changes limited to cases where the user explicitly asks for Windows support.