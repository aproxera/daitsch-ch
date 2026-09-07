# Schweizer Layer

Dieser Fork trägt auf dem Branch `ch-layer` einen Aufsatz über den
Upstream-Katalog von [lord-helicon/daitsch](https://github.com/lord-helicon/daitsch).
`main` bleibt unverändert am Upstream, damit Pull Requests dorthin sauber
abzweigen können.

## Was der Layer ändert

- **Schweizer Rechtschreibung**, ss statt Eszett, durchgehend.
- **Erkennung schreibungstolerant.** 15 Regeln enthielten selbst ein
  Eszett und hätten Schweizer Texte nie gefunden. Jetzt `(?:ß|ss)`.
- **Vier neue Muster:** `deutsche-anfuehrungszeichen`, `belege-erfunden`,
  `beleg-traegt-nicht`, `chatbot-zitierreste`. Katalog 74 → 78.

`tools/ch_layer.py` legt den Layer über den Katalog. Das Skript ist
idempotent, mehrfaches Ausführen schadet nicht.

## Nach einem Upstream-Merge

    git merge upstream/main
    python tools/ch_layer.py
    python skills/daitsch/scripts/klartext.py --selbsttest
    # Version in beiden Manifesten erhöhen, siehe unten
    git commit -am "Upstream x.y.z gemergt, CH-Layer neu aufgelegt"
    git push origin ch-layer

## Version: eigene Linie, und sie muss steigen

Der Fork führt eine **eigene Versionsnummer**, eine Minor über dem
gemergten Upstream-Stand. Upstream 1.2.3 wurde hier 1.3.0. Kommt Upstream
auf 1.3.0, wird daraus hier 1.4.0.

Das ist keine Kosmetik. Der Marketplace `aproxera/skills` bindet dieses
Repo als `url`-Source auf `ref: ch-layer` ein, und Claude Code legt das
Plugin im Cache unter seiner Versionsnummer ab. **Bleibt die Version
gleich, kann ein neuer Commit als Update unerkannt bleiben** und die
Mitarbeitenden arbeiten weiter mit der alten Fassung. Darum bei jeder
Änderung, die ausgeliefert werden soll, die Version erhöhen — in
`.claude-plugin/plugin.json` **und** `.claude-plugin/marketplace.json`.

Kontrolle nach dem Push:

    claude plugin marketplace update aproxera
    claude plugin update daitsch@aproxera
    claude plugin details daitsch@aproxera

## Warum HTTPS und nicht SSH

Der Marketplace-Eintrag nutzt eine `url`-Source mit `https://`, nicht die
naheliegendere `github`-Source. Die klont über SSH; wo kein Host-Key in
`known_hosts` steht und kein Key im Agent liegt, bricht die Installation
mit `Host key verification failed` ab, und einen Fallback auf HTTPS gibt
es dort nicht. Dieses Repo ist öffentlich, über HTTPS braucht der Clone
also keine Zugangsdaten und auf den Clients kein SSH.

## Der PR an Upstream

Noch offen: der Fix in `install.ps1` (Commit `d06ecc2`) gehört als
eigener Pull Request an `lord-helicon/daitsch`. Weg: von `main`
abzweigen, cherry-picken, pushen, PR gegen `lord-helicon/daitsch:main`.
Der CH-Layer gehört **nicht** in diesen PR.
