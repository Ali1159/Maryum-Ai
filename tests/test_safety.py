from maryum_ai.safety import RiskLevel, classify_action


def test_allowlisted_action_is_safe():
    decision = classify_action("open_application")
    assert decision.allowed is True
    assert decision.risk == RiskLevel.SAFE


def test_destructive_action_requires_confirmation():
    decision = classify_action("delete")
    assert decision.allowed is False
    assert decision.risk == RiskLevel.CONFIRM


def test_unknown_action_is_blocked():
    decision = classify_action("run_any_shell")
    assert decision.allowed is False
    assert decision.risk == RiskLevel.CONFIRM
