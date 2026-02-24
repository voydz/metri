# IMPLEMENTATION_PLAN.md

## Project: `metri` CLI
**Goal:** Create a Python-based CLI tool named `metri` to log and query health/fitness metrics (e.g., FTP, weight, body fat) in a local SQLite database. It must identically mirror the architecture, tooling, and release pipeline of `nutri`.

**Architecture & Tooling (Nutri Parity):**
- **Language:** Python 3.11+
- **Package Manager:** `uv` (no raw pip/venv)
- **Structure:** `src/metricli/` module structure with `pyproject.toml`
- **Linting & Formatting:** `ruff`
- **Testing:** `pytest`
- **Build Tool:** `PyInstaller` (creating a standalone `arm64` macOS binary)
- **CI/CD:** GitHub Actions (Release triggers a build and automatically bumps a Homebrew tap)
- **Database:** SQLite 3 stored at `~/.local/share/metri/metrics.db` (Append-only pattern)

---

## Phase 1: Setup & `uv` Project Initialization
**IST-Zustand:** Leeres Verzeichnis.
**SOLL-Zustand:** Ein initialisiertes `uv` Projekt mit korrekter Ordnerstruktur und Makefile.

- [ ] Führe `uv init` aus und passe die `pyproject.toml` an (Name: `metri`, Version: `0.1.0`).
- [ ] Füge Dependencies in `pyproject.toml` hinzu (z.B. `tabulate`).
- [ ] Füge Dev-Dependencies hinzu: `ruff`, `pytest`, `pyinstaller`.
- [ ] Erstelle die Verzeichnisstruktur: `src/metricli/` mit `__init__.py` und `__main__.py`.
- [ ] Erstelle ein `Makefile` analog zu `nutri` (Targets: `setup`, `run`, `lint`, `lint-fix`, `test`, `build`, `smoke`, `package`).
- [ ] Definiere das `build` Target im Makefile, das `uv run pyinstaller --onefile --name metri --target-arch arm64 src/metricli/__main__.py` aufruft.

## Phase 2: Database Layer (`db.py`)
**IST-Zustand:** Keine Logik vorhanden.
**SOLL-Zustand:** Eine robuste SQLite-Anbindung in `src/metricli/db.py`.

- [ ] Implementiere die Logik, um `~/.local/share/metri/` anzulegen.
- [ ] Schreibe eine Funktion zur Datenbank-Initialisierung.
- [ ] Erstelle das Schema (Append-only, keine Upserts):
  ```sql
  CREATE TABLE metrics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date TEXT NOT NULL,       -- 'YYYY-MM-DD'
      time TEXT NOT NULL,       -- 'HH:MM:SS'
      metric_key TEXT NOT NULL, -- 'ftp_watts', 'weight_kg', etc.
      value REAL NOT NULL,
      source TEXT,              -- 'garmin', 'home_assistant', 'manual'
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(date);
  CREATE INDEX IF NOT EXISTS idx_metrics_key ON metrics(metric_key);
  ```

## Phase 3: CLI Router & Command Logic
**IST-Zustand:** Leere `__main__.py`.
**SOLL-Zustand:** Vollständiges CLI-Interface mit Argument Parsing.

- [ ] Implementiere `argparse` in `__main__.py` für Subcommands: `log`, `today`, `query`, `delete`.
- [ ] Füge `--format [table|json]` als globale Option hinzu.
- [ ] **Befehl `log`**: `--key` (str), `--value` (float), `--source` (str, default: 'manual'), `--date`, `--time`. Führt INSERT aus.
- [ ] **Befehl `delete`**: Erwartet ID, löscht Eintrag.
- [ ] **Befehl `today`**: Holt Einträge für das heutige Datum, Output als Tabelle/JSON.
- [ ] **Befehl `query`**: `--last <N>d`, `--avg`. Holt historische Daten, optional aggregiert.

## Phase 4: Linting, Testing & Smoke-Test
**IST-Zustand:** Code ist geschrieben, aber ungetestet.
**SOLL-Zustand:** Sauberer Code, der als isoliertes Binary funktioniert.

- [ ] Richte `ruff` in der `pyproject.toml` ein. Führe `make lint-fix` aus.
- [ ] Schreibe 1-2 Basis-Tests für die DB-Logik in `tests/test_db.py`.
- [ ] Führe `make build` aus, um das PyInstaller-Binary in `dist/metri` zu erzeugen.
- [ ] Führe den im Makefile definierten `make smoke` Test aus (führt das Binary in einer sauberen, leeren Umgebung aus, um sicherzustellen, dass keine Python-Abhängigkeiten leaken).

## Phase 5: GitHub Actions & Homebrew Release Pipeline
**IST-Zustand:** Lokales Binary.
**SOLL-Zustand:** Automatisierter Release-Prozess per GitHub Actions.

- [ ] Erstelle `.github/workflows/release.yml` (exakte Kopie der `nutri` Pipeline).
- [ ] Der Workflow muss auf `release: types: [published]` triggern.
- [ ] Schritte im Workflow:
  1. Setup `macos-14` runner.
  2. Setup `uv`.
  3. `make build` und `make package` ausführen (tar.gz inkl. sha256 erstellen).
  4. Asset in das GitHub Release hochladen.
  5. **Homebrew Bump**: Führe `brew tap <dein-github-name>/homebrew-tap` und `brew bump-formula-pr <dein-github-name>/tap/metri` aus, um den Release automatisch an dein privates Homebrew Repo zu pushen.

---
**Hinweis für den Coding Agent:**
Halte dich strikt an die `uv` und `Makefile` Pattern des Projekts. Das Ziel ist eine 100%ige Tooling-Parität zu `nutri`, damit Pflege und Deployment der beiden Tools komplett identisch ablaufen.