# 01 — Estructura del proyecto

Este documento describe la organización de archivos del proyecto, el stack tecnológico y cómo fluye una ejecución de tests de inicio a fin.

---

## Tabla de contenidos

1. [Árbol de archivos](#árbol-de-archivos)
2. [Responsabilidad de cada archivo](#responsabilidad-de-cada-archivo)
3. [Stack tecnológico](#stack-tecnológico)
4. [Flujo de ejecución completo](#flujo-de-ejecución-completo)

---

## Árbol de archivos

```
AcademyGit/
│
├── tests/
│   └── test_login.py          ← casos E2E de login
│
├── pages/
│   └── login_page.py          ← Page Object del login
│
├── data/
│   └── users.py               ← datos de prueba (credenciales)
│
├── utils/
│   └── config.py              ← configuración global (URL, timeout)
│
├── reports/
│   ├── academy_report.css     ← tema visual del reporte HTML
│   ├── PYTEST_HTML_REPORT.md  ← documentación del reporte HTML
│   └── report.html            ← reporte generado (ignorado por git)
│
├── docs/
│   ├── README.md              ← índice de documentación
│   ├── 01-PROJECT_STRUCTURE.md
│   ├── 02-PAGE_OBJECT_MODEL.md
│   ├── 03-CONFTEST_AND_HOOKS.md
│   ├── 04-ALLURE_REPORT.md
│   ├── 05-CI_CD.md
│   └── exercises/
│       ├── README.md
│       ├── 01-CUSTOMIZE_REPORT_CSS.md
│       ├── 02-RUNNING_REPORTS.md
│       └── 03-EXTEND_PAGE_OBJECTS.md
│
├── .github/
│   └── workflows/
│       └── e2e.yml            ← pipeline de CI/CD
│
├── conftest.py                ← hooks de pytest (reportes, screenshots)
├── pytest.ini                 ← configuración base de pytest
├── requirements.txt           ← dependencias Python
├── README.md                  ← documentación principal del repo
├── TESTING.md                 ← guía operativa de ejecución
└── ALLURE_SETUP.md            ← guía de configuración de Allure
```

---

## Responsabilidad de cada archivo

### `tests/test_login.py`

Contiene los **casos de prueba E2E**. Cada función `test_*` es un escenario de usuario:

- `test_valid_login` — login con credenciales correctas, verifica redirección al inventario.
- `test_login_error_messages_for_invalid_scenarios` — login con usuario bloqueado y credenciales inválidas, verifica mensajes de error.

Los tests no tienen lógica de interacción con el navegador: delegan todo al Page Object.

### `pages/login_page.py`

Es el **Page Object** de la pantalla de login. Encapsula todos los locators y acciones. Los tests interactúan con la UI únicamente a través de este objeto.

Ver [02 — Page Object Model](02-PAGE_OBJECT_MODEL.md) para la explicación completa.

### `data/users.py`

Diccionarios con credenciales de prueba. Permite cambiar datos sin tocar los tests.

```python
STANDARD_USER = {"username": "standard_user", "password": "secret_sauce"}
LOCKED_USER   = {"username": "locked_out_user", "password": "secret_sauce"}
INVALID_USER  = {"username": "invalid_user", "password": "wrong_password"}
```

### `utils/config.py`

Constantes globales compartidas por toda la suite:

```python
BASE_URL = "https://www.saucedemo.com/"
DEFAULT_TIMEOUT_MS = 10000
```

Centralizar estos valores evita que estén hardcodeados en múltiples archivos.

### `conftest.py`

Archivo especial de pytest, cargado automáticamente antes de cualquier test. Aquí se definen:

- Hooks que personalizan el reporte HTML (título, metadatos, dashboard, screenshots).
- Integración con Allure (adjuntar screenshot en fallos).

Ver [03 — conftest.py y hooks](03-CONFTEST_AND_HOOKS.md) para la explicación detallada.

### `pytest.ini`

```ini
[pytest]
addopts = -v --tb=short --browser chromium --alluredir=allure-results
testpaths = tests
python_files = test_*.py
pythonpath = .
```

- `addopts`: flags aplicados en cada ejecución por defecto.
- `testpaths`: carpeta donde buscar tests.
- `pythonpath = .`: permite imports relativos desde la raíz (`from pages.login_page import ...`).

### `requirements.txt`

```
playwright
pytest
pytest-playwright
pytest-html
allure-pytest
```

Cada dependencia tiene una razón:

| Paquete | Rol |
|---------|-----|
| `playwright` | Librería para controlar el browser |
| `pytest` | Framework de testing |
| `pytest-playwright` | Fixture `page` y opciones `--browser`, `--headed` |
| `pytest-html` | Genera el reporte HTML con `--html` |
| `allure-pytest` | Genera datos Allure con `--alluredir` y habilita decoradores |

### `reports/academy_report.css`

CSS personalizado que sobreescribe el estilo de pytest-html. Aplica el tema oscuro con tipografías de Google Fonts y los componentes del dashboard (tarjetas, banner).

### `.github/workflows/e2e.yml`

Pipeline de GitHub Actions. Ejecuta los tests en cada push/PR a `main`/`master`, genera ambos reportes y publica Allure en GitHub Pages.

Ver [05 — CI/CD](05-CI_CD.md).

---

## Stack tecnológico

```
┌─────────────────────────────────────────────────┐
│               CAPA DE REPORTES                  │
│   pytest-html + academy_report.css              │
│   allure-pytest → allure serve                  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│             CAPA DE TESTS (pytest)              │
│   test_login.py                                 │
│   conftest.py (hooks, fixtures)                 │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│         CAPA DE PAGE OBJECTS (POM)              │
│   pages/login_page.py                           │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│           CAPA DE BROWSER (Playwright)          │
│   pytest-playwright → Chromium                  │
└─────────────────────────────────────────────────┘
```

### Por qué pytest

pytest es el estándar de facto para Python. Ventajas sobre unittest:
- Sintaxis limpia (funciones, no clases obligatorias).
- Fixtures potentes (`page`, `browser`).
- Ecosistema de plugins (`pytest-playwright`, `pytest-html`, `allure-pytest`).
- Parametrización con `@pytest.mark.parametrize`.

### Por qué Playwright (y no Selenium)

| Característica | Playwright | Selenium |
|----------------|-----------|----------|
| API | Moderna, async-first | Legada, verbosa |
| Auto-wait | Nativo | Manual (explicit waits) |
| Instalación browsers | `playwright install` | WebDriver separado |
| Capturas | `page.screenshot()` | Requiere configuración |
| Velocidad | Más rápido | Más lento |

### Por qué dos sistemas de reportes

| Reporte | Cuándo usarlo |
|---------|---------------|
| pytest-html | Revisión rápida, archivo único descargable, sin dependencias externas |
| Allure | Historial entre ejecuciones, pasos detallados, clasificación por features/stories, publicación en Pages |

---

## Flujo de ejecución completo

```
1. pytest se inicia
      │
      ▼
2. Lee pytest.ini → aplica addopts
      │
      ▼
3. Carga conftest.py automáticamente
   └── registra hooks (título, metadatos, screenshot, etc.)
      │
      ▼
4. Descubre tests en tests/test_login.py
      │
      ▼
5. Para cada test:
   ├── SETUP:   pytest-playwright abre Chromium, crea fixture `page`
   ├── CALL:    ejecuta la función test_*
   │             └── instancia LoginPage(page)
   │                   └── llama métodos (goto, login_as, assert_*)
   │                         └── Playwright interactúa con el browser
   └── TEARDOWN: si falló → hook captura screenshot → adjunta a reporte
      │
      ▼
6. pytest_sessionfinish: calcula duración total
      │
      ▼
7. pytest-html genera reports/report.html
   └── inyecta CSS de academy_report.css
   └── llama hooks: título, metadatos, dashboard (banner + tarjetas)
      │
      ▼
8. allure-pytest escribe JSON en allure-results/
      │
      ▼
9. (opcional) allure serve allure-results → reporte interactivo en browser
```
