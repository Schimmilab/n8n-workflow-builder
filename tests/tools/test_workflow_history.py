"""Tests fuer get_workflow_history / get_workflow_version.

Entstanden 2026-09-01 aus dem API-Abgleich nach dem Update auf n8n 2.36.9:
Von 37 neuen Endpunkten war die Versionshistorie der einzige, den eine
Community-Instanz ueberhaupt nutzen darf.
"""
import pytest
from unittest.mock import AsyncMock
from n8n_workflow_builder.tools.workflow_tools import WorkflowTools


@pytest.fixture
def workflow_tools(deps):
    return WorkflowTools(deps=deps)


def _wf(nodes, name="Testflow"):
    return {"id": "abc123", "name": name, "nodes": [{"name": n} for n in nodes]}


def _ver(vid, created, autor="schimmi"):
    return {"versionId": vid, "createdAt": created, "authors": autor}


async def test_history_lists_versions_newest_first(workflow_tools, mock_n8n_client):
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(["A"]))
    mock_n8n_client.get_workflow_history = AsyncMock(return_value=[
        _ver("alt", "2025-01-01T10:00:00Z"),
        _ver("neu", "2026-01-01T10:00:00Z"),
    ])
    text = (await workflow_tools.handle("get_workflow_history", {"workflow_id": "abc123"}))[0].text
    assert "2 version(s)" in text
    # NEWEST FIRST: die neuere versionId muss vor der aelteren stehen
    assert text.index("neu") < text.index("alt")


async def test_history_empty_says_so(workflow_tools, mock_n8n_client):
    """NEGATIVKONTROLLE: keine Versionen ist kein Fehler, aber auch keine Tabelle."""
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(["A"]))
    mock_n8n_client.get_workflow_history = AsyncMock(return_value=[])
    text = (await workflow_tools.handle("get_workflow_history", {"workflow_id": "abc123"}))[0].text
    assert "No version history" in text
    assert "versionId" not in text


async def test_history_403_reports_licence_not_api_error(workflow_tools, mock_n8n_client):
    """NEGATIVKONTROLLE: 403 ist eine Lizenzaussage, kein technischer Fehler.
    Auf Community-Instanzen antworten mehrere neue Endpunkte so — das muss
    unterscheidbar bleiben, sonst sucht jemand einen Bug, der keiner ist."""
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(["A"]))
    mock_n8n_client.get_workflow_history = AsyncMock(side_effect=Exception("403: Forbidden"))
    with pytest.raises(Exception) as exc:
        await workflow_tools.handle("get_workflow_history", {"workflow_id": "abc123"})
    assert "NOT_LICENSED" in str(exc.value)


async def test_version_diff_reports_both_directions(workflow_tools, mock_n8n_client):
    """Positivfall: entfernte UND hinzugekommene Nodes werden genannt."""
    mock_n8n_client.get_workflow_version = AsyncMock(
        return_value={"versionId": "v1", "createdAt": "2025-01-01T10:00:00Z",
                      "nodes": [{"name": "Alt"}, {"name": "Bleibt"}]})
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(["Bleibt", "Neu"]))
    text = (await workflow_tools.handle(
        "get_workflow_version", {"workflow_id": "abc123", "version_id": "v1"}))[0].text
    # ⛔ ZUORDNUNG pruefen, nicht Anwesenheit: bei vertauschten Diff-Richtungen
    #    stehen beide Namen weiterhin im Text, nur unter der falschen Ueberschrift.
    #    Genau daran ist dieser Test am 01.09. beim Muss-rot-Versuch durchgefallen.
    weg_pos = text.index("Existed then, gone now")
    neu_pos = text.index("Added since")
    assert weg_pos < text.index("Alt") < neu_pos, "Alt steht nicht im Entfernt-Block"
    assert neu_pos < text.index("Neu"), "Neu steht nicht im Hinzugefuegt-Block"
    assert "Bleibt" not in text.split("Compared to now")[1]


async def test_version_identical_node_set_warns_about_parameters(workflow_tools, mock_n8n_client):
    """NEGATIVKONTROLLE gegen eine falsche Entwarnung: gleiche Node-NAMEN
    heissen nicht gleicher Inhalt. Ohne diesen Hinweis liest sich das Ergebnis
    als 'nichts geaendert', obwohl Parameter nicht verglichen wurden."""
    mock_n8n_client.get_workflow_version = AsyncMock(
        return_value={"versionId": "v1", "nodes": [{"name": "A"}]})
    mock_n8n_client.get_workflow = AsyncMock(return_value=_wf(["A"]))
    text = (await workflow_tools.handle(
        "get_workflow_version", {"workflow_id": "abc123", "version_id": "v1"}))[0].text
    assert "Same node set" in text
    assert "not compared" in text and "parameters" in text


async def test_missing_params_raise(workflow_tools, mock_n8n_client):
    with pytest.raises(Exception):
        await workflow_tools.handle("get_workflow_history", {})
    with pytest.raises(Exception):
        await workflow_tools.handle("get_workflow_version", {"workflow_id": "abc123"})
