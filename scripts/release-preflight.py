#!/usr/bin/env python3
"""Prueft vor einem Release, ob die Doku zum Code passt.

⛔ Warum es das gibt (2026-09-01, Schimmi):
   Zwei Releases an einem Abend (v1.24.0, v1.25.0) — und die README nannte
   danach immer noch v1.23.1 vom 14.03. und keines der vier neuen Tools.
   Es war die ZWEITE Instanz derselben Klasse in drei Tagen: am 29.08. hing
   die README des oura-mcp-server drei Minor-Versionen hinterher.

   Schimmis Frage dazu war die richtige: "das ist irgendwie der Grund, warum
   du da keinen kleinen Workflow fuer den Release hast?" — Nach Top-Regel 7
   ist bei einem zweimal gerissenen Vorsatz nicht die Disziplin die offene
   Frage, sondern das fehlende Werkzeug.

🎯 Der Kern-Check ist der letzte: JEDER in server.py definierte Tool-Name muss
   irgendwo in der README vorkommen. Eine Fassung, die Faehigkeiten nur in
   Prosa beschreibt, besteht ihn nicht — wer nach "activate_workflow" sucht,
   findet dort sonst nichts.

Aufruf:  python3 scripts/release-preflight.py [--selftest]
Exit 0 alles passt · 1 Befund · 2 Selbsttest gefallen
"""
import argparse
import pathlib
import re
import subprocess
import sys
import tomllib

WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _version(wurzel):
    return tomllib.loads((wurzel / "pyproject.toml").read_text())["project"]["version"]


def _tool_namen(wurzel):
    """Alle in server.py definierten Tool-Namen."""
    quelle = (wurzel / "src" / "n8n_workflow_builder" / "server.py").read_text()
    return sorted(set(re.findall(r'name="([a-z_][a-z0-9_]*)"', quelle)))


def pruefe(wurzel):
    befunde = []
    v = _version(wurzel)

    changelog = (wurzel / "CHANGELOG.md").read_text()
    if f"[{v}]" not in changelog:
        befunde.append(f"CHANGELOG.md hat keinen Eintrag fuer {v}")

    rel = wurzel / "releases" / f"v{v}.md"
    if not rel.exists():
        befunde.append(f"releases/v{v}.md fehlt")

    readme = (wurzel / "README.md").read_text()
    if v not in readme:
        befunde.append(f"README.md nennt Version {v} nicht (steht dort noch eine aeltere?)")

    # ⭐ Der eigentliche Fang
    # ⚠️ Baseline: 39 Tools standen am 01.09. noch nie in der README. Sie alle
    #    zu melden haette den Check nach dem zweiten Release unlesbar gemacht —
    #    dieselbe Ueberlegung wie bei song-luecken-bekannt.txt und
    #    bekannt-ohne-karte.txt im Vault. Gemeldet wird, was NEU fehlt.
    #    ⛔ Die vier Tools des Anlassfalls stehen bewusst NICHT drin: eine
    #    Baseline, die ihren eigenen Anlassfall stillschaltet, schafft sich ab.
    bekannt = set()
    bl = wurzel / "scripts" / "readme-luecken-bekannt.txt"
    if bl.exists():
        bekannt = {z.strip() for z in bl.read_text().split("\n")
                   if z.strip() and not z.startswith("#")}
    fehlend = [t for t in _tool_namen(wurzel) if t not in readme and t not in bekannt]
    if fehlend:
        zeige = ", ".join(fehlend[:8]) + (" …" if len(fehlend) > 8 else "")
        befunde.append(f"{len(fehlend)} Tool(s) nicht in der README: {zeige}")

    return v, befunde


def selftest():
    """Positiv- UND Negativkontrolle an einem kuenstlichen Repo.

    ⛔ Die Negativkontrolle ist der Punkt: Ein Preflight, der IMMER meldet,
       besteht jeden Positivtest und wird nach dem zweiten Release ignoriert.
    """
    import tempfile, json
    fehler = []

    def pruef(name, ok):
        print(f"  {'✅' if ok else '⛔'} {name}")
        if not ok:
            fehler.append(name)

    def baue(tmp, readme_text, tools=("alpha", "beta")):
        w = pathlib.Path(tmp)
        (w / "src" / "n8n_workflow_builder").mkdir(parents=True, exist_ok=True)
        (w / "releases").mkdir(exist_ok=True)
        (w / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "9.9.9"\n')
        (w / "CHANGELOG.md").write_text("## [9.9.9] - 2026-01-01\n")
        (w / "releases" / "v9.9.9.md").write_text("notes\n")
        (w / "README.md").write_text(readme_text)
        quelle = "\n".join(f'Tool(\n    name="{t}",\n)' for t in tools)
        (w / "src" / "n8n_workflow_builder" / "server.py").write_text(quelle)
        return w

    # POSITIV: alles vollstaendig -> muss schweigen
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 9.9.9\nTools: alpha, beta\n")
        _, b = pruefe(w)
        pruef("vollstaendiges Repo schweigt", not b)

    # NEGATIV 1: ein Tool fehlt in der README
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 9.9.9\nTools: alpha\n")
        _, b = pruefe(w)
        pruef("fehlendes Tool wird gemeldet", any("beta" in x for x in b))

    # NEGATIV 2: README nennt eine alte Version — der Anlassfall von heute
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 1.0.0\nTools: alpha, beta\n")
        _, b = pruefe(w)
        pruef("veraltete Version in der README wird gemeldet",
              any("nennt Version" in x for x in b))

    # NEGATIV 4: ein Tool auf der Baseline darf NICHT gemeldet werden
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 9.9.9\nTools: alpha\n")
        (w / "scripts").mkdir(exist_ok=True)
        (w / "scripts" / "readme-luecken-bekannt.txt").write_text("# bekannt\nbeta\n")
        _, b = pruefe(w)
        pruef("Tool auf der Baseline schweigt", not any("beta" in x for x in b))

    # NEGATIV 5: ein NEUES Tool wird trotz Baseline gemeldet
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 9.9.9\nTools: alpha\n", tools=("alpha", "beta", "gamma"))
        (w / "scripts").mkdir(exist_ok=True)
        (w / "scripts" / "readme-luecken-bekannt.txt").write_text("# bekannt\nbeta\n")
        _, b = pruefe(w)
        pruef("neues Tool wird trotz Baseline gemeldet", any("gamma" in x for x in b))

    # NEGATIV 3: releases/-Datei fehlt
    with tempfile.TemporaryDirectory() as t:
        w = baue(t, "Version 9.9.9\nTools: alpha, beta\n")
        (w / "releases" / "v9.9.9.md").unlink()
        _, b = pruefe(w)
        pruef("fehlende Release-Notiz wird gemeldet", any("releases/" in x for x in b))

    print("\n" + ("✅ Selbsttest bestanden" if not fehler
                  else "⛔ FEHLGESCHLAGEN: " + ", ".join(fehler)))
    return 0 if not fehler else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    v, befunde = pruefe(WURZEL)
    if not befunde:
        print(f"✅ Release-Preflight fuer v{v}: Doku passt zum Code "
              f"({len(_tool_namen(WURZEL))} Tools geprueft).")
        sys.exit(0)

    print(f"⛔ Release-Preflight fuer v{v} — {len(befunde)} Befund(e):\n")
    for b in befunde:
        print(f"  · {b}")
    print("\nErst beheben, dann taggen. Sonst steht in der README wieder eine "
          "Version, die es nicht mehr gibt.")
    sys.exit(1)


if __name__ == "__main__":
    main()
