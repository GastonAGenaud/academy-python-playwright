# Academy E2E Automation (Python + Playwright)

---

## #ES

Proyecto de automatización E2E orientado a capacitación, usando `pytest` + `playwright` con patrón **Page Object Model (POM)**.

### Objetivo del repositorio

- Validar flujos de login en SauceDemo.
- Separar responsabilidades entre tests, page objects, datos y configuración.
- Ejecutar pruebas localmente y en CI con reporte HTML.

### Stack técnico

- Python
- Pytest
- Playwright para Python
- pytest-playwright
- pytest-html

### Estructura del repo y para qué sirve cada archivo

- `.github/workflows/e2e.yml`
  - Pipeline de GitHub Actions.
  - Instala dependencias, instala navegador Chromium y ejecuta tests.
  - Publica `report.html` como artifact (`e2e-report`).

- `tests/test_login.py`
  - Casos E2E de autenticación.
  - Incluye:
    - login válido
    - escenarios negativos parametrizados (usuario bloqueado y credenciales inválidas)

- `pages/login_page.py`
  - Page Object de la pantalla de login.
  - Encapsula locators, acciones y aserciones para evitar duplicación en tests.

- `data/users.py`
  - Datos de prueba reutilizables (usuarios).
  - Permite mantener tests limpios y sin credenciales hardcodeadas en cada caso.

- `utils/config.py`
  - Configuración global: `BASE_URL` y timeout por defecto.

- `pytest.ini`
  - Configuración base de pytest:
    - argumentos por defecto
    - carpeta de tests
    - patrón de archivos
    - `pythonpath`

- `requirements.txt`
  - Dependencias Python necesarias para ejecutar el proyecto.

- `TESTING.md`
  - Guía operativa para correr tests, generar reportes HTML, usar Inspector/trace y entender limitaciones del modo UI en Python.

### Métodos principales (LoginPage)

En `pages/login_page.py`:

- `goto()`
  - Navega a `BASE_URL` y aplica timeout por defecto.

- `login(username, password)`
  - Completa credenciales y hace click en login.

- `login_as(user)`
  - Variante de `login` que recibe un diccionario `{username, password}`.

- `assert_login_loaded()`
  - Verifica que seguimos en pantalla de login.

- `assert_inventory_loaded()`
  - Verifica login exitoso (redirect a `inventory.html`).

- `assert_error_contains(message)`
  - Verifica mensaje de error esperado en login fallido.

### Buenas prácticas aplicadas

- **POM** para centralizar interacciones con la UI.
- **Test data separada** en `data/users.py`.
- **Parametrización** con `pytest.param(..., id=...)` para casos legibles.
- **Aserciones claras** de resultado esperado por escenario.
- **Configuración centralizada** en `utils/config.py`.

### Comandos útiles

Desde la raíz del proyecto:

```bash
python -m pytest tests/
```

Solo login:

```bash
python -m pytest tests/test_login.py -v
```

Generar reporte HTML:

```bash
python -m pytest tests/ --html=reports/report.html --self-contained-html
```

Debug con Playwright Inspector (PowerShell):

```bash
$env:PWDEBUG=1; python -m pytest tests/test_login.py -s
```

### Ejecución en CI

El workflow se dispara en push y pull request a `main`/`master`.

Para ver el reporte en GitHub Actions:

1. Entrar al workflow run.
2. Abrir job `e2e`.
3. Descargar artifact `e2e-report`.
4. Abrir `report.html`.

---

## #EN

E2E automation project for training, using `pytest` + `playwright` with the **Page Object Model (POM)** pattern.

### Repository goals

- Validate login flows on SauceDemo.
- Separate concerns between tests, page objects, data, and configuration.
- Run tests locally and in CI with HTML report.

### Tech stack

- Python
- Pytest
- Playwright for Python
- pytest-playwright
- pytest-html

### Repo structure and what each file does

- `.github/workflows/e2e.yml`
  - GitHub Actions pipeline.
  - Installs dependencies, Chromium browser, and runs tests.
  - Publishes `report.html` as artifact (`e2e-report`).

- `tests/test_login.py`
  - Login E2E cases.
  - Includes:
    - valid login
    - parametrized negative scenarios (locked user and invalid credentials)

- `pages/login_page.py`
  - Login screen Page Object.
  - Encapsulates locators, actions, and assertions to avoid duplication in tests.

- `data/users.py`
  - Reusable test data (users).
  - Keeps tests clean and free of hardcoded credentials.

- `utils/config.py`
  - Global config: `BASE_URL` and default timeout.

- `pytest.ini`
  - Base pytest config:
    - default options
    - test folder
    - file pattern
    - `pythonpath`

- `requirements.txt`
  - Python dependencies required to run the project.

- `TESTING.md`
  - How to run tests, generate HTML reports, use Inspector/trace, and UI mode limitations in Python.

### Main methods (LoginPage)

In `pages/login_page.py`:

- `goto()`
  - Navigates to `BASE_URL` and sets default timeout.

- `login(username, password)`
  - Fills credentials and clicks login.

- `login_as(user)`
  - `login` variant that takes a `{username, password}` dict.

- `assert_login_loaded()`
  - Asserts we are still on the login screen.

- `assert_inventory_loaded()`
  - Asserts successful login (redirect to `inventory.html`).

- `assert_error_contains(message)`
  - Asserts the expected error message on failed login.

### Practices applied

- **POM** to centralize UI interactions.
- **Separate test data** in `data/users.py`.
- **Parametrization** with `pytest.param(..., id=...)` for readable cases.
- **Clear assertions** for expected outcome per scenario.
- **Centralized config** in `utils/config.py`.

### Useful commands

From project root:

```bash
python -m pytest tests/
```

Login tests only:

```bash
python -m pytest tests/test_login.py -v
```

Generate HTML report:

```bash
python -m pytest tests/ --html=reports/report.html --self-contained-html
```

Debug with Playwright Inspector (PowerShell):

```bash
$env:PWDEBUG=1; python -m pytest tests/test_login.py -s
```

### CI execution

The workflow runs on push and pull request to `main`/`master`.

To view the report in GitHub Actions:

1. Open the workflow run.
2. Open the `e2e` job.
3. Download the `e2e-report` artifact.
4. Open `report.html`.
