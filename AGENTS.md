# Agent Guidance

## Project shape

- This is a Windows-focused Python utility for converting image contours into
  screen-coordinate mouse drawing paths.
- `src/image_processor.py` loads an image or clipboard image, detects edges,
  extracts and simplifies contours, then writes a preview PNG and a paths JSON.
- `src/mouse_drawer.py` loads the paths JSON, maps image coordinates to a
  user-selected screen rectangle, runs a cursor-only test, and can then draw
  with PyAutoGUI.
- `src/app.py` is a small standalone smoke/demo entry point and is not the
  documented workflow or PyInstaller entry point.
- Read [README.md](README.md) for the complete CLI workflow and build steps.

## Commands and validation

- Run commands from the repository root because relative paths such as
  `images/clipboard.png` and `images/auto_paths.json` are working-directory
  relative.
- Dependencies are listed in [requirements.txt](requirements.txt). There is no
  automated test suite; use focused Python checks or `python -m compileall src`
  for non-GUI validation.
- The supported executable build is `./build_exe.ps1` from PowerShell. It uses
  PyInstaller with `src/mouse_drawer.py` as the console entry point and writes
  `dist/DrawShit.exe`.
- Preserve the existing CLI forms and JSON shape unless the task explicitly
  changes the public interface: `{ "paths": [...], "path_count": N }`.

## Auto-approval boundaries

- When auto approval is enabled, approve read-only inspection, documentation
  edits, syntax checks, and other deterministic local validation automatically.
- Do not automatically run commands that start live mouse movement or drawing,
  including `python src/mouse_drawer.py`, the built EXE, or code paths invoking
  PyAutoGUI. These require an explicit user decision and a visible target
  drawing area.
- Treat clipboard capture, global keyboard hooks, package installation, and
  PyInstaller builds as side-effectful operations requiring explicit approval.
- Never bypass the built-in safety controls: PyAutoGUI fail-safe, ESC abort,
  cursor-only test, and the staged ENTER confirmation before real drawing.

## Implementation conventions

- Keep changes small and procedural unless a task requires a larger design.
- Use 4-space indentation, module-level constants for tunable drawing/image
  parameters, UTF-8 JSON, and the existing German user-facing messages.
- Keep generated previews, clipboard images, path JSON, `build/`, and `dist/`
  separate from source changes unless the task explicitly targets an artifact.
- For image-processing changes, validate both the generated preview and the
  paths JSON when practical. For coordinate or drawing changes, prefer pure
  mapping/validation checks and avoid unattended desktop automation.