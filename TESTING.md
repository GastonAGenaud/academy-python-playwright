# Tests E2E (Playwright + pytest)

---

## #ES

### Requisitos

- Python 3 con venv activado
- Dependencias: `pip install -r requirements.txt`
- Navegadores Playwright: `playwright install chromium` (si no se instalaron antes)

### Ejecutar todos los tests E2E

Desde la raíz del proyecto (`d:\Academy`):

```bash
pytest tests/
```

O con más detalle:

```bash
pytest tests/ -v --headed --browser chromium
```

### Ejecutar E2E con reporte HTML

Para generar un reporte HTML al finalizar (útil para CI o revisión manual):

```bash
pytest tests/ --html=report.html --self-contained-html
```

- `report.html`: archivo de salida (puedes usar otra ruta, ej. `reports/e2e-report.html`).
- `--self-contained-html`: incluye CSS y datos en un solo HTML; así puedes abrir el archivo sin carpeta de assets.

Abrir el reporte: abre `report.html` en el navegador (doble clic o `start report.html` en Windows).

### ¿Por qué no funciona `pytest --ui`?

El **UI Mode** (timeline, watch mode, test explorer en ventana) con `--ui` **solo existe en el test runner de Node/TypeScript** (`npx playwright test --ui`). El plugin oficial **pytest-playwright no implementa `--ui`**; en Python esa opción no existe. Artículos que dicen "pytest --ui" para Python suelen estar mezclando con la versión Node.

### Depurar con interfaz en Python: Inspector y trace

#### 1. Playwright Inspector (paso a paso, Pick locator)

Equivalente práctico a "UI" en Python: abre el Inspector y el navegador.

```bash
# Windows (PowerShell)
$env:PWDEBUG=1; pytest tests/ -s

# Windows (CMD)
set PWDEBUG=1 && pytest tests/ -s

# Linux / macOS
PWDEBUG=1 pytest tests/ -s
```

- Se abre el **Playwright Inspector** (paso a paso, "Pick locator", ver DOM).
- `-s` evita que pytest capture stdout.
- Un solo test: `$env:PWDEBUG=1; pytest tests/test_login.py -s -k test_valid_login`

#### 2. Trace viewer (time travel después de ejecutar)

Grabás un trace y lo abrís en una UI tipo "time travel":

```bash
pytest tests/ --tracing=on --headed
```

Si algo falla, el trace se guarda en `test-results/`. Luego:

```bash
playwright show-trace test-results/.../trace.zip
```

(Abrís el `.zip` del test que falló; la ruta sale en el log de pytest.)

#### Variantes útiles

```bash
# Reporte en una carpeta y con timestamp
pytest tests/ --html=reports/e2e-report.html --self-contained-html

# Sin abrir el navegador (headless), ideal para CI
pytest tests/ --html=report.html --self-contained-html --headed=false
```

### Estructura

- `tests/`: tests E2E (pytest + Playwright).
- `pages/`: Page Objects (ej. `LoginPage`).
- `data/`: datos de prueba (usuarios, etc.).
- `utils/`: configuración (BASE_URL, timeouts).

Los tests usan la app de demo [Sauce Demo](https://www.saucedemo.com/) (`utils/config.py`).

### CI (GitHub Actions)

El workflow `.github/workflows/e2e.yml` ejecuta los E2E en cada push/PR a `main` o `master` y guarda el reporte HTML como artifact.

**Ver el reporte:** en la run de Actions → job "e2e" → al final, en **Artifacts** descargá `e2e-report` (contiene `report.html`). El artifact se sube siempre (aunque falle el job) y se conserva 30 días.

---

## #EN

### Requirements

- Python 3 with venv activated
- Dependencies: `pip install -r requirements.txt`
- Playwright browsers: `playwright install chromium` (if not installed before)

### Run all E2E tests

From project root (`d:\Academy`):

```bash
pytest tests/
```

Or with more detail:

```bash
pytest tests/ -v --headed --browser chromium
```

### Run E2E with HTML report

To generate an HTML report when finished (useful for CI or manual review):

```bash
pytest tests/ --html=report.html --self-contained-html
```

- `report.html`: output file (you can use another path, e.g. `reports/e2e-report.html`).
- `--self-contained-html`: embeds CSS and data in a single HTML file so you can open it without an assets folder.

To open the report: open `report.html` in your browser (double-click or `start report.html` on Windows).

### Why doesn't `pytest --ui` work?

**UI Mode** (timeline, watch mode, test explorer window) with `--ui` **only exists in the Node/TypeScript test runner** (`npx playwright test --ui`). The official **pytest-playwright plugin does not implement `--ui`**; in Python that option does not exist. Articles that mention "pytest --ui" for Python are usually mixing it with the Node version.

### Debug with a UI in Python: Inspector and trace

#### 1. Playwright Inspector (step-by-step, Pick locator)

Practical equivalent to "UI" in Python: opens the Inspector and the browser.

```bash
# Windows (PowerShell)
$env:PWDEBUG=1; pytest tests/ -s

# Windows (CMD)
set PWDEBUG=1 && pytest tests/ -s

# Linux / macOS
PWDEBUG=1 pytest tests/ -s
```

- Opens the **Playwright Inspector** (step-by-step, "Pick locator", view DOM).
- `-s` prevents pytest from capturing stdout.
- Single test: `$env:PWDEBUG=1; pytest tests/test_login.py -s -k test_valid_login`

#### 2. Trace viewer (time travel after running)

Record a trace and open it in a time-travel UI:

```bash
pytest tests/ --tracing=on --headed
```

If something fails, the trace is saved in `test-results/`. Then:

```bash
playwright show-trace test-results/.../trace.zip
```

(Open the `.zip` of the failed test; the path appears in the pytest log.)

#### Useful variants

```bash
# Report in a folder with timestamp
pytest tests/ --html=reports/e2e-report.html --self-contained-html

# Without opening the browser (headless), ideal for CI
pytest tests/ --html=report.html --self-contained-html --headed=false
```

### Structure

- `tests/`: E2E tests (pytest + Playwright).
- `pages/`: Page Objects (e.g. `LoginPage`).
- `data/`: test data (users, etc.).
- `utils/`: configuration (BASE_URL, timeouts).

Tests use the demo app [Sauce Demo](https://www.saucedemo.com/) (`utils/config.py`).

### GitHub Actions (CI)

The workflow `.github/workflows/e2e.yml` runs E2E on every push/PR to `main` or `master` and saves the HTML report as an artifact.

**View the report:** in the Actions run → "e2e" job → at the end, under **Artifacts** download `e2e-report` (contains `report.html`). The artifact is uploaded always (even if the job fails) and is kept for 30 days.
