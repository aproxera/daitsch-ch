#!/usr/bin/env python3
"""Legt den Schweizer Layer über den Katalog von daitsch.

Das Skript ist wiederholbar. Nach jedem Merge von upstream einmal laufen
lassen, dann das Ergebnis einchecken:

    python3 tools/ch_layer.py
    python3 skills/daitsch/scripts/klartext.py --selbsttest

Es tut vier Dinge:

1. Erkennung wird schreibungstolerant. Regeln, die ein ß enthalten, finden
   danach auch die Schweizer Fassung. `heißt` findet `heisst`, `außerdem`
   findet `ausserdem`. Ohne diesen Schritt ist der Prüfer in der Schweiz
   für einen Teil seiner eigenen Muster blind.
2. Der Fließtext des Skills wird auf Schweizer Rechtschreibung gestellt.
3. Anführungszeichen werden auf Guillemets umgestellt, «so», und die
   deutsche Form „so“ wird als weicher Befund aufgenommen.
4. Drei Muster kommen dazu, die im Katalog fehlen: erfundene Belege,
   Belege die ihre Aussage nicht tragen, Zitierreste aus Chatbots.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SKILL = WURZEL / "skills" / "daitsch"
KATALOG = SKILL / "references" / "katalog.md"

MARKE = "<!-- CH-LAYER -->"

BLOCK = re.compile(r"^```(\w+)[ \t]*\n(.*?)\n```", re.MULTILINE | re.DOTALL)


# ------------------------------------------------------------ 1. Erkennung


def regex_tolerant(quelle: str) -> str:
    """ß in einem Ausdruck so umschreiben, dass beide Schreibungen passen.

    Zeichenklassen bleiben unangetastet: in [\\wäöüß] deckt \\w die Schweizer
    Fassung schon ab, und eine Gruppe darf dort nicht stehen.
    """
    # Erst zurück auf den Ausgangsstand, damit ein zweiter Lauf nicht
    # (?:(?:ß|ss)|ss) erzeugt.
    quelle = quelle.replace("(?:ß|ss)", "ß")

    raus: list[str] = []
    in_klasse = False
    vorher = ""
    for zeichen in quelle:
        if zeichen == "[" and vorher != "\\":
            in_klasse = True
        elif zeichen == "]" and vorher != "\\":
            in_klasse = False
        if zeichen == "ß" and not in_klasse:
            raus.append("(?:ß|ss)")
        else:
            raus.append(zeichen)
        vorher = zeichen
    return "".join(raus)


def wortliste_tolerant(block: str) -> str:
    zeilen = block.splitlines()
    raus: list[str] = []
    for zeile in zeilen:
        raus.append(zeile)
        if "ß" in zeile:
            ch = zeile.replace("ß", "ss")
            if ch not in zeilen:
                raus.append(ch)
    return "\n".join(raus)


def bloecke_anpassen(text: str) -> str:
    def ersetzen(treffer: re.Match) -> str:
        art, rumpf = treffer.group(1), treffer.group(2)
        if art == "regex":
            rumpf = "\n".join(regex_tolerant(z) for z in rumpf.splitlines())
        elif art == "wortliste":
            rumpf = wortliste_tolerant(rumpf)
        return f"```{art}\n{rumpf}\n```"

    return BLOCK.sub(ersetzen, text)


# --------------------------------------------------------- 2./3. Fließtext


def prosa_umstellen(text: str, guillemets: bool = True) -> str:
    """Fließtext auf Schweizer Rechtschreibung, Codeblöcke unberührt."""
    stuecke = re.split(r"(^```\w*[ \t]*\n.*?\n```)", text, flags=re.MULTILINE | re.DOTALL)
    raus: list[str] = []
    for i, stueck in enumerate(stuecke):
        if i % 2 == 1:  # Codeblock
            raus.append(stueck)
            continue
        stueck = stueck.replace("ß", "ss")
        if guillemets:
            stueck = stueck.replace("\u201e", "\u00ab").replace("\u201c", "\u00bb")
        raus.append(stueck)
    return "".join(raus)


NEUE_MUSTER = """
<!-- CH-LAYER -->

## Schweiz

### deutsche-anfuehrungszeichen

**Erkennung:** Die deutschen Anführungszeichen \u201esind so\u201c sind im
bundesdeutschen Satz richtig, im Schweizer Satz nicht. Hier stehen Guillemets,
«so». Gemischte Formen in einem Text verraten eine übernommene Vorlage.

**Härte:** weich

```regex
\u201e[^\u201c\\n]{2,80}\u201c
```

**Floskel:** Der Kollege nannte das Vorgehen \u201ealternativlos\u201c.

**Klartext:** Der Kollege nannte das Vorgehen «alternativlos».

**Zulässig:** In wörtlich übernommenen Zitaten aus deutschen Quellen und in
Texten, die ausdrücklich für ein deutsches Publikum gesetzt werden.

## Belege

### belege-erfunden

**Erkennung:** Quelle, Titel, Autor, Jahr, Link, ISBN oder DOI klingen
stimmig, existieren aber nicht. Das Modell füllt eine Lücke mit einer
plausiblen Form statt mit einer Angabe. Maschinell nicht zu finden: jede
Fundstelle muss nachgeschlagen werden.

**Härte:** hart

**Floskel:** Laut einer Studie der ETH Zürich aus dem Jahr 2023 sinkt der
Aufwand um vierzig Prozent.

**Klartext:** Wie stark der Aufwand sinkt, ist nicht erhoben. Die Zahl fehlt.

**Zulässig:** Nie. Eine Lücke wird als Lücke benannt, nicht gefüllt.

### beleg-traegt-nicht

**Erkennung:** Die Quelle gibt es, sie sagt aber etwas anderes. Dazu gehören
eine gültige DOI zu einem anderen Aufsatz, ein Buch zum verwandten statt zum
genannten Thema, ein Buchbeleg ohne Seitenzahl, ein Link auf eine
Trefferliste statt auf das Dokument, und ein Eintrag im Quellenverzeichnis,
an dem keine Aussage hängt.

**Härte:** weich

**Floskel:** Der Bericht des BFS belegt den Rückgang. [Link auf die Suchseite
des BFS]

**Klartext:** Der Rückgang steht in der Erhebung des BFS von 2024, Tabelle 3.

**Zulässig:** Wenn die Quelle als Hintergrund und nicht als Beleg für eine
einzelne Aussage gesetzt ist und der Text das kenntlich macht.

## Artefakte

### chatbot-zitierreste

**Erkennung:** Zitier- und Trackingreste aus der Oberfläche eines Chatbots
sind im Text geblieben.

Der Ausdruck deckt die Reste im Fliesstext ab. Reste im Linkziel findet er
nicht: der Prüfer maskiert URLs, bevor er sucht, damit Adressen nicht jede
zweite Prosaregel auslösen. Der häufigste Rest steckt aber genau dort, als
`utm_source=chatgpt.com`. Vor dem Veröffentlichen deshalb zusätzlich:

    grep -nE "utm_source=(chatgpt|claude|perplexity)" datei.md

**Härte:** hart

```regex
(?i)(oaicite|:contentReference|turn\\d+search|\\[cite:\\s*\\d+\\]|\\[span_\\d+\\]|grok_render_citation)
```

**Floskel:** Die Zahl stammt aus dem Bericht :contentReference[oaicite:3]{index=3}.

**Klartext:** Die Zahl stammt aus dem Jahresbericht 2025, Seite 12.

**Zulässig:** Nie im ausgelieferten Text. In einer Sammlung von Rohmaterial
darf der Rest stehen bleiben, solange sie als solche gekennzeichnet ist.
"""


def anfuehrungsregel_reparieren(text: str) -> str:
    """Die Regel gerade-anfuehrungszeichen soll auf Guillemets zeigen."""
    alt_erkennung = (
        "**Erkennung:** Gerade Anführungszeichen in deutschem Text sind "
        "durchgereichte englische Konvention."
    )
    for variante in (
        "Deutsch ist «so» oder »so«.",
        "Deutsch ist \u201eso\u201c oder »so«.",
    ):
        text = text.replace(
            f"{alt_erkennung} {variante}",
            f"{alt_erkennung} Im Schweizer Satz stehen Guillemets, «so».",
        )
    return text


def main() -> int:
    if not KATALOG.exists():
        print(f"Katalog nicht gefunden: {KATALOG}", file=sys.stderr)
        return 2

    katalog = KATALOG.read_text(encoding="utf-8")

    # Der eigene Block wird nicht mitverarbeitet. Sonst stellt der zweite Lauf
    # die Anführungszeichen im Beispiel der Regel deutsche-anfuehrungszeichen
    # um, und die Regel findet ihr eigenes Beispiel nicht mehr.
    katalog = katalog.split(MARKE)[0].rstrip()

    katalog = bloecke_anpassen(katalog)
    katalog = prosa_umstellen(katalog)
    katalog = anfuehrungsregel_reparieren(katalog)
    katalog = katalog.rstrip() + "\n" + NEUE_MUSTER
    KATALOG.write_text(katalog, encoding="utf-8")

    weitere = [
        SKILL / "SKILL.md",
        SKILL / "references" / "pruefliste.md",
        SKILL / "tests" / "floskelig.md",
        SKILL / "tests" / "klartext.md",
    ]
    weitere += sorted((SKILL / "tests" / "metriken").glob("*.md"))
    for pfad in weitere:
        if pfad.exists():
            pfad.write_text(prosa_umstellen(pfad.read_text(encoding="utf-8")), encoding="utf-8")

    print("CH-Layer gelegt. Jetzt den Selbsttest laufen lassen:")
    print("  python3 skills/daitsch/scripts/klartext.py --selbsttest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
