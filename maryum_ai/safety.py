from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RiskLevel(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"


CONFIRMATION_ACTIONS = {
    "delete",
    "install_package",
    "sudo",
    "shutdown",
    "reboot",
    "system_settings",
    "network_sensitive",
}

ALLOWED_ACTIONS = {
    "open_application",
    "set_volume",
    "list_files",
    "search_files",
    "run_script",
}


@dataclass(slots=True)
class ActionDecision:
    allowed: bool
    risk: RiskLevel
    reason: str
    confirmable: bool = False


def classify_action(action: str) -> ActionDecision:
    normalized = action.strip().lower()
    if normalized in CONFIRMATION_ACTIONS:
        return ActionDecision(
            allowed=False,
            risk=RiskLevel.CONFIRM,
            reason="Action requires explicit user confirmation in GUI",
            confirmable=True,
        )

    if normalized in ALLOWED_ACTIONS:
        return ActionDecision(
            allowed=True,
            risk=RiskLevel.SAFE,
            reason="Action is allowlisted",
            confirmable=False,
        )

    return ActionDecision(
        allowed=False,
        risk=RiskLevel.CONFIRM,
        reason="Action not allowlisted",
        confirmable=False,
    )


def assert_within_directory(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False
