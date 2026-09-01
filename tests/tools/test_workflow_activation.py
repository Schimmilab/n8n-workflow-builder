"""Tests fuer activate_workflow / deactivate_workflow.

Entstanden 2026-09-01. Die Mocks fuer client.activate_workflow lagen seit
jeher in conftest.py — die Methoden gab es aber weder im Client noch als
Tool. Ein Mock kann nicht fehlschlagen, deshalb war das nie aufgefallen.
"""
import pytest
from unittest.mock import AsyncMock
from n8n_workflow_builder.tools.workflow_tools import WorkflowTools


@pytest.fixture
def workflow_tools(deps):
    return WorkflowTools(deps=deps)


def _wf(active: bool, name="Testflow", wid="abc123"):
    return {"id": wid, "name": name, "active": active}


async def test_activate_flips_flag(workflow_tools, mock_n8n_client):
    """Positivfall: inaktiv -> aktiv, und die Antwort nennt beide Zustaende."""
    mock_n8n_client.get_workflow = AsyncMock(side_effect=[_wf(False), _wf(True)])
    out = await workflow_tools.handle("activate_workflow", {"workflow_id": "abc123"})
    text = out[0].text
    assert "Activated" in text
    assert "False → True" in text
    mock_n8n_client.activate_workflow.assert_awaited_once_with("abc123")


async def test_deactivate_flips_flag(workflow_tools, mock_n8n_client):
    mock_n8n_client.get_workflow = AsyncMock(side_effect=[_wf(True), _wf(False)])
    out = await workflow_tools.handle("deactivate_workflow", {"workflow_id": "abc123"})
    assert "Deactivated" in out[0].text
    mock_n8n_client.deactivate_workflow.assert_awaited_once_with("abc123")


async def test_already_in_target_state_sends_nothing(workflow_tools, mock_n8n_client):
    """NEGATIVKONTROLLE: schon aktiv -> es darf KEIN Request rausgehen."""
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(True))
    out = await workflow_tools.handle("activate_workflow", {"workflow_id": "abc123"})
    assert "No change needed" in out[0].text
    mock_n8n_client.activate_workflow.assert_not_awaited()


async def test_accepted_but_not_applied_raises(workflow_tools, mock_n8n_client):
    """NEGATIVKONTROLLE, der eigentliche Grund fuer die Vorher/Nachher-Messung:
    n8n antwortet 200, der Flag springt aber nicht um. Das MUSS auffallen —
    ein 'success' aus einem Statuscode waere genau der stille Ausfall."""
    mock_n8n_client.get_workflow = AsyncMock(side_effect=[_wf(False), _wf(False)])
    with pytest.raises(Exception) as exc:
        await workflow_tools.handle("activate_workflow", {"workflow_id": "abc123"})
    assert "STATE_NOT_APPLIED" in str(exc.value) or "still" in str(exc.value)


async def test_missing_id_raises(workflow_tools, mock_n8n_client):
    with pytest.raises(Exception):
        await workflow_tools.handle("activate_workflow", {})
