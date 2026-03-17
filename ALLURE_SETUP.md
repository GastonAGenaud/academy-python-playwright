# Guía de implementación: Allure Report

Esta guía te permite implementar **Allure Report** en el proyecto de automatización E2E paso a paso.  
Todos los bloques de código están listos para copiar y pegar.

---

## Tabla de contenidos

1. [¿Qué es Allure Report?](#qué-es-allure-report)
2. [Prerequisitos](#prerequisitos)
3. [Archivos a modificar](#archivos-a-modificar)
   - [requirements.txt](#1-requirementstxt)
   - [pytest.ini](#2-pytestini)
   - [conftest.py](#3-conftestpy)
   - [pages/login_page.py](#4-pageslogin_pagepy)
   - [tests/test_login.py](#5-teststest_loginpy)
   - [.github/workflows/e2e.yml](#6-githubworkflowse2eyml)
4. [Ejecución local](#ejecución-local)
5. [Cómo abrir el reporte](#cómo-abrir-el-reporte)
6. [Qué esperar en el reporte](#qué-esperar-en-el-reporte)

---

## ¿Qué es Allure Report?

Allure es un framework de reportes para pruebas automatizadas. A diferencia de pytest-html, Allure genera:

- Reporte interactivo con suites, historial y tendencias.
- Vista de pasos dentro de cada test (con tiempos).
- Capturas de pantalla adjuntas directamente en el paso que falló.
- Clasificación de tests por Feature / Story / Severity.
- Integración con CI/CD para historial acumulado entre ejecuciones.

---

## Prerequisitos

### Java 8 o superior (requerido para generar el reporte HTML)

Verificar que Java está instalado:

```bash
java -version
```

Si no lo tienes: https://adoptium.net/

### Allure CLI (herramienta de línea de comandos)

**Windows (con Scoop):**

```powershell
scoop install allure
```

**Windows (con Chocolatey):**

```powershell
choco install allure
```

**macOS (con Homebrew):**

```bash
brew install allure
```

Verificar instalación:

```bash
allure --version
```

---

## Archivos a modificar

### 1. `requirements.txt`

Agregar la dependencia `allure-pytest`. El archivo completo queda así:

```text
playwright
pytest
pytest-playwright
pytest-html
allure-pytest
```

---

### 2. `pytest.ini`

Agregar `--alluredir=allure-results` en `addopts` para que cada ejecución genere los datos del reporte automáticamente.

El archivo completo queda así:

```ini
[pytest]
# Headless by default (CI). Use: pytest --headed for local browser UI
addopts = -v --tb=short --browser chromium --alluredir=allure-results
testpaths = tests
python_files = test_*.py
pythonpath = .
```

> **Nota:** `allure-results/` es la carpeta donde Allure guarda los archivos JSON intermedios. El reporte HTML se genera en un segundo paso con `allure serve` o `allure generate`.

---

### 3. `conftest.py`

Se agregan dos cosas:
- `allure.attach()` en el hook de fallo para adjuntar el screenshot al reporte.
- Importar `allure` al inicio del archivo.

El archivo completo queda así:

```python
"""
Pytest hooks para reporte HTML (pytest-html) y Allure Report:
título, metadatos, dashboard, screenshots en fallo.
"""

from __future__ import annotations

import html
import time

import allure
import pytest

from utils.config import BASE_URL


def pytest_html_report_title(report) -> None:
    report.title = "Academy E2E — Test Report"


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Extra rows in Environment (pytest-metadata)."""
    if not config.getoption("htmlpath", default=None):
        return
    try:
        from pytest_metadata.plugin import metadata_key

        if metadata_key not in config.stash:
            return
        meta = config.stash[metadata_key]
        meta["Project"] = "Academy E2E Automation"
        meta["Target app"] = "SauceDemo"
        meta["BASE_URL"] = BASE_URL
        meta["Stack"] = "Python · pytest · Playwright · POM"
    except Exception:
        pass


def pytest_html_results_summary(prefix, summary, postfix, session) -> None:
    """Dashboard cards + banner above the default summary."""
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    passed = failed = skipped = errors = 0
    if tr and hasattr(tr, "stats"):
        passed = len(tr.stats.get("passed", []))
        failed = len(tr.stats.get("failed", []))
        skipped = len(tr.stats.get("skipped", []))
        errors = len(tr.stats.get("error", []))
    total = passed + failed + skipped + errors
    duration = getattr(session, "_sessionduration", None)
    if duration is None:
        duration = time.time() - getattr(session, "_starttime", time.time())
    dur_s = f"{duration:.1f}s"

    banner = (
        '<div class="academy-banner">'
        "<strong>Academy E2E</strong> — Reporte generado para capacitación en automatización. "
        "Los tests fallidos incluyen <strong>captura de pantalla</strong> en la fila (Links / extras). "
        f"URL bajo prueba: <code>{html.escape(BASE_URL)}</code>"
        "</div>"
    )
    dash = f"""
    <div class="academy-dashboard">
      <div class="academy-card academy-card--total">
        <div class="academy-card__value">{total}</div>
        <div class="academy-card__label">Total</div>
      </div>
      <div class="academy-card academy-card--pass">
        <div class="academy-card__value">{passed}</div>
        <div class="academy-card__label">Passed</div>
      </div>
      <div class="academy-card academy-card--fail">
        <div class="academy-card__value">{failed + errors}</div>
        <div class="academy-card__label">Failed / Error</div>
      </div>
      <div class="academy-card academy-card--skip">
        <div class="academy-card__value">{skipped}</div>
        <div class="academy-card__label">Skipped</div>
      </div>
      <div class="academy-card">
        <div class="academy-card__value">{html.escape(dur_s)}</div>
        <div class="academy-card__label">Duration</div>
      </div>
    </div>
    """
    prefix.insert(0, banner + dash)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Adjunta screenshot en pytest-html Y en Allure cuando un test con `page` falla."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return

    try:
        png_bytes = page.screenshot(full_page=False)
    except Exception:
        return

    # --- Adjuntar en Allure Report ---
    allure.attach(
        png_bytes,
        name="Screenshot on failure",
        attachment_type=allure.attachment_type.PNG,
    )

    # --- Adjuntar en pytest-html ---
    try:
        import pytest_html.extras as html_extras
        extra = html_extras.png(png_bytes, "Screenshot on failure")
        rep.extra = getattr(rep, "extra", []) + [extra]
    except ImportError:
        pass


def pytest_sessionstart(session: pytest.Session) -> None:
    session._starttime = time.time()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    session._sessionduration = time.time() - getattr(session, "_starttime", time.time())
```

---

### 4. `pages/login_page.py`

Se agrega `@allure.step` en cada método público para que Allure muestre los pasos ejecutados dentro de cada test.

El archivo completo queda así:

```python
import allure
from playwright.sync_api import Page, expect

from utils.config import BASE_URL, DEFAULT_TIMEOUT_MS


class LoginPage:
    """Page Object for SauceDemo login screen."""

    def __init__(self, page: Page):
        """Create page locators once to reuse them across tests."""
        self.page = page
        self.username_input = page.locator("//input[@id='user-name']")
        self.password_input = page.locator("//input[@id='password']")
        self.login_button = page.locator("//input[@id='login-button']")
        self.error_message = page.locator("//h3[@data-test='error']")

    @allure.step("Navegar a la página de login")
    def goto(self):
        """Open login URL and configure a default timeout for interactions."""
        self.page.goto(BASE_URL)
        self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    @allure.step("Ingresar credenciales: usuario={username}, contraseña={password}")
    def login(self, username: str, password: str):
        """Perform login using raw credentials."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    @allure.step("Iniciar sesión como usuario")
    def login_as(self, user: dict) -> None:
        """Perform login using a user dictionary with username/password keys."""
        self.login(user["username"], user["password"])

    @allure.step("Verificar que la página de login está cargada")
    def assert_login_loaded(self) -> None:
        """Assert that the browser is still on the login screen."""
        expect(self.page).to_have_url(BASE_URL)
        expect(self.page).to_have_title("Swag Labs")

    @allure.step("Verificar redirección al inventario tras login exitoso")
    def assert_inventory_loaded(self) -> None:
        """Assert successful authentication redirect to inventory page."""
        expect(self.page).to_have_url(f"{BASE_URL}inventory.html")
        expect(self.page).to_have_title("Swag Labs")

    @allure.step("Verificar que el mensaje de error contiene: '{message}'")
    def assert_error_contains(self, message: str) -> None:
        """Assert that the visible login error message includes expected text."""
        expect(self.error_message).to_contain_text(message)
```

---

### 5. `tests/test_login.py`

Se agregan los decoradores de Allure para estructurar el reporte:

- `@allure.epic` — nivel más alto (nombre del proyecto)
- `@allure.feature` — funcionalidad bajo prueba
- `@allure.story` — historia de usuario / escenario
- `@allure.severity` — prioridad del test
- `@allure.title` — nombre descriptivo que aparece en el reporte

El archivo completo queda así:

```python
"""Login end-to-end tests following Page Object Model conventions."""

import allure
import pytest

from data.users import INVALID_USER, LOCKED_USER, STANDARD_USER
from pages.login_page import LoginPage


@allure.epic("SauceDemo E2E")
@allure.feature("Login")
@allure.story("Login exitoso con usuario estándar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Usuario estándar puede iniciar sesión y accede al inventario")
def test_valid_login(page):
    """Validate that a standard user can access the inventory page."""
    login_page = LoginPage(page)

    login_page.goto()
    login_page.login_as(STANDARD_USER)

    login_page.assert_inventory_loaded()


@allure.epic("SauceDemo E2E")
@allure.feature("Login")
@allure.story("Manejo de errores en login")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    ("user_data", "expected_error"),
    [
        pytest.param(
            LOCKED_USER,
            "Epic sadface: Sorry, this user has been locked out.",
            id="locked_user_cannot_log_in",
        ),
        pytest.param(
            INVALID_USER,
            "Epic sadface: Username and password do not match any user in this service",
            id="invalid_credentials_show_error",
        ),
    ],
)
@allure.title("Login inválido muestra mensaje de error correcto")
def test_login_error_messages_for_invalid_scenarios(page, user_data, expected_error):
    """Validate login error handling for locked and invalid users."""
    login_page = LoginPage(page)

    login_page.goto()
    login_page.login_as(user_data)

    login_page.assert_error_contains(expected_error)
```

---

### 6. `.github/workflows/e2e.yml`

El workflow actualizado:
1. Ejecuta los tests generando `allure-results/`.
2. Genera el reporte Allure HTML con la action `simple-elf/allure-report-action`.
3. Publica el reporte en **GitHub Pages** de forma automática.
4. También sube `allure-results` como artifact descargable por si falla la publicación.

El archivo completo queda así:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

# Permisos necesarios para publicar en GitHub Pages
permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  e2e:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install Playwright browsers
        run: playwright install chromium --with-deps

      - name: Run E2E tests (with Allure results)
        run: |
          pytest tests/ \
            --alluredir=allure-results \
            --html=reports/report.html \
            --self-contained-html \
            --css=reports/academy_report.css \
            -v \
            --browser=chromium
        # `always()` garantiza que el reporte se genere incluso si hay tests fallidos
        continue-on-error: true

      - name: Upload allure-results artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: allure-results
          path: allure-results/
          retention-days: 30

      - name: Upload HTML report artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-html-report
          path: reports/report.html
          retention-days: 30

      - name: Generate Allure HTML report
        uses: simple-elf/allure-report-action@v1
        if: always()
        with:
          allure_results: allure-results
          allure_report: allure-report
          allure_history: allure-history
          keep_reports: 20

      - name: Publish Allure report to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        if: always()
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_branch: gh-pages
          publish_dir: allure-report
```

> **Para activar GitHub Pages:** En tu repositorio ve a **Settings → Pages → Source** y selecciona la rama `gh-pages`. El reporte quedará disponible en:  
> `https://<tu-usuario>.github.io/<nombre-del-repo>/`

---

## Ejecución local

### Paso 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Ejecutar los tests

```bash
pytest
```

Esto genera la carpeta `allure-results/` con los archivos JSON del reporte.

### Paso 3: Ver el reporte en el navegador

```bash
allure serve allure-results
```

Allure levanta un servidor local y abre el reporte automáticamente en el navegador.

### Alternativa: generar reporte estático

```bash
allure generate allure-results --clean -o allure-report
allure open allure-report
```

---

## Cómo abrir el reporte

| Entorno | Comando / URL |
|---|---|
| Local (servidor) | `allure serve allure-results` |
| Local (estático) | `allure open allure-report` |
| CI (artifact) | Descargar artifact `allure-results` desde la pestaña **Actions** |
| CI (GitHub Pages) | `https://<usuario>.github.io/<repo>/` |

---

## Qué esperar en el reporte

Una vez abierto `allure serve allure-results`, verás:

### Sección Overview
- Gráfico de dona con porcentaje de tests passed/failed/broken.
- Línea de tiempo de ejecución.

### Sección Suites
Organizado por los decoradores:

```
SauceDemo E2E (epic)
  └── Login (feature)
        ├── Login exitoso con usuario estándar (story)
        │     └── test_valid_login
        │           ├── [paso] Navegar a la página de login
        │           ├── [paso] Iniciar sesión como usuario 'standard_user'
        │           └── [paso] Verificar redirección al inventario
        └── Manejo de errores en login (story)
              ├── locked_user_cannot_log_in
              └── invalid_credentials_show_error
```

### En un test fallido
- Se muestra el stack trace completo.
- La captura de pantalla aparece como attachment en la sección **Tear Down**.

---

## Resumen de cambios

| Archivo | Cambio |
|---|---|
| `requirements.txt` | Agregar `allure-pytest` |
| `pytest.ini` | Agregar `--alluredir=allure-results` en `addopts` |
| `conftest.py` | Importar `allure`, adjuntar screenshot con `allure.attach()` en fallo |
| `pages/login_page.py` | Importar `allure`, decorar métodos con `@allure.step(...)` |
| `tests/test_login.py` | Importar `allure`, decorar tests con `@allure.epic/feature/story/severity/title` |
| `.github/workflows/e2e.yml` | Agregar steps de Allure: generación, artifact y GitHub Pages |

---

> **Tip para la clase:** Al ejecutar `allure serve allure-results` por primera vez, si los tests están todos en verde, podés forzar un fallo cambiando temporalmente una URL o credencial para ver cómo se adjunta el screenshot en el reporte.
