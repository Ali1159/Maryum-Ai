from pathlib import Path

from maryum_ai.tools import SafeAutomationTools


def test_list_files(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")

    tools = SafeAutomationTools(tmp_path)
    result = tools.run("list_files", directory=str(tmp_path))

    assert result.ok is True
    assert sorted(result.data["items"]) == ["a.txt", "b.txt"]


def test_search_files(tmp_path: Path):
    (tmp_path / "report-2026.txt").write_text("x", encoding="utf-8")
    (tmp_path / "note.md").write_text("x", encoding="utf-8")

    tools = SafeAutomationTools(tmp_path)
    result = tools.run("search_files", directory=str(tmp_path), query="report")

    assert result.ok is True
    assert len(result.data["items"]) == 1
    assert "report-2026.txt" in result.data["items"][0]


def test_run_script_only_from_allowlist(tmp_path: Path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    script = scripts_dir / "hello.sh"
    script.write_text("#!/usr/bin/env bash\necho hello\n", encoding="utf-8")
    script.chmod(0o755)

    tools = SafeAutomationTools(scripts_dir)
    ok = tools.run("run_script", name="hello.sh")
    blocked = tools.run("run_script", name="../outside.sh")

    assert ok.ok is True
    assert "hello" in (ok.data or {}).get("stdout", "")
    assert blocked.ok is False


def test_confirmable_action_generates_pending_request(tmp_path: Path):
    tools = SafeAutomationTools(tmp_path)
    request = tools.request("shutdown")
    assert request.ok is False
    assert "confirmation_id" in (request.data or {})

    denied = tools.confirm(request.data["confirmation_id"], approved=False)
    assert denied.ok is False
    assert "cancelled" in denied.message.lower()
