from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .safety import assert_within_directory, classify_action


@dataclass(slots=True)
class ToolResult:
    ok: bool
    message: str
    data: dict[str, Any] | None = None


@dataclass(slots=True)
class PendingAction:
    action: str
    params: dict[str, Any]


class SafeAutomationTools:
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir.expanduser().resolve()
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self._pending: dict[str, PendingAction] = {}

    def request(self, action: str, **params: Any) -> ToolResult:
        decision = classify_action(action)
        if decision.confirmable:
            confirmation_id = str(uuid.uuid4())
            self._pending[confirmation_id] = PendingAction(action=action, params=params)
            return ToolResult(
                False,
                f"Confirmation required for action: {action}",
                {"confirmation_id": confirmation_id},
            )

        return self.run(action, **params)

    def confirm(self, confirmation_id: str, approved: bool) -> ToolResult:
        pending = self._pending.pop(confirmation_id, None)
        if not pending:
            return ToolResult(False, "No such pending action")
        if not approved:
            return ToolResult(False, "Action cancelled by user")

        return ToolResult(
            False,
            (
                "Confirmed action remains blocked in MVP. Use trusted local scripts in "
                "the allowlisted script directory for privileged workflows."
            ),
        )

    def run(self, action: str, **params: Any) -> ToolResult:
        decision = classify_action(action)
        if not decision.allowed:
            return ToolResult(False, f"Blocked: {decision.reason}")

        method = getattr(self, f"_tool_{action}", None)
        if not method:
            return ToolResult(False, "Tool not implemented")

        try:
            return method(**params)
        except Exception as exc:  # pragma: no cover - defensive
            return ToolResult(False, f"Tool failed: {exc}")

    def _tool_open_application(self, app: str) -> ToolResult:
        app = app.strip()
        if not app:
            return ToolResult(False, "Missing app name")

        resolved = shutil.which(app)
        if not resolved:
            return ToolResult(False, f"Application not found: {app}")

        subprocess.Popen([resolved], start_new_session=True)
        return ToolResult(True, f"Opened {app}", {"app": app})

    def _tool_set_volume(self, percent: int | str) -> ToolResult:
        value = int(percent)
        if value < 0 or value > 100:
            return ToolResult(False, "Volume must be between 0 and 100")

        pactl = shutil.which("pactl")
        if not pactl:
            return ToolResult(False, "pactl is not installed")

        subprocess.run([pactl, "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"], check=True)
        return ToolResult(True, f"Volume set to {value}%", {"volume": value})

    def _tool_list_files(self, directory: str = "~", limit: int = 50) -> ToolResult:
        root = Path(directory).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return ToolResult(False, "Directory does not exist")

        items = sorted(p.name for p in root.iterdir())[: max(1, min(limit, 200))]
        return ToolResult(True, f"Listed {len(items)} files", {"items": items})

    def _tool_search_files(self, directory: str = "~", query: str = "", limit: int = 50) -> ToolResult:
        if not query.strip():
            return ToolResult(False, "Missing query")

        root = Path(directory).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return ToolResult(False, "Directory does not exist")

        matches: list[str] = []
        q = query.lower()
        for path in root.rglob("*"):
            if len(matches) >= max(1, min(limit, 200)):
                break
            if q in path.name.lower():
                matches.append(str(path))

        return ToolResult(True, f"Found {len(matches)} matches", {"items": matches})

    def _tool_run_script(self, name: str, args: str = "") -> ToolResult:
        safe_name = os.path.basename(name)
        script_path = (self.scripts_dir / safe_name).resolve()

        if not assert_within_directory(self.scripts_dir, script_path):
            return ToolResult(False, "Script path is outside allowlist directory")
        if not script_path.exists():
            return ToolResult(False, "Script not found")
        if not os.access(script_path, os.X_OK):
            return ToolResult(False, "Script is not executable")

        parsed_args = shlex.split(args)
        proc = subprocess.run(
            [str(script_path), *parsed_args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        ok = proc.returncode == 0
        msg = "Script executed" if ok else "Script failed"
        return ToolResult(ok, msg, {"stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]})
