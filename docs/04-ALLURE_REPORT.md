# 04 — Allure Report

Este documento explica qué es Allure, cómo está integrado en este proyecto, cómo se ejecuta localmente y en CI, y las diferencias con pytest-html.

---

## Tabla de contenidos

1. [¿Qué es Allure?](#qué-es-allure)
2. [Diferencias con pytest-html](#diferencias-con-pytest-html)
3. [Prerequisitos](#prerequisitos)
4. [Integración en el proyecto](#integración-en-el-proyecto)
5. [Decoradores de Allure](#decoradores-de-allure)
6. [Cómo funciona la generación del reporte](#cómo-funciona-la-generación-del-reporte)
7. [Ejecución local](#ejecución-local)
8. [Qué se ve en el reporte](#qué-se-ve-en-el-reporte)
9. [Allure en CI: GitHub Actions](#allure-en-ci-github-actions)

---

## ¿Qué es Allure?

Allure es un framework de reportes para pruebas automatizadas. A diferencia de pytest-html (que genera un único HTML estático), Allure genera un reporte interactivo con:

- Gráfico de dona con porcentaje de passed/failed/broken.
- Vista de **pasos** dentro de cada test (con tiempos por paso).
- Capturas de pantalla adjuntas en el paso que falló.
- Clasificación de tests por **Epic / Feature / Story**.
- Nivel de severidad por test.
- Historial acumulado entre ejecuciones (en CI).

---

## Diferencias con pytest-html

| Característica | pytest-html | Allure |
|----------------|------------|--------|
| Formato de salida | Un solo `.html` portable | Carpeta con JSON + HTML generado |
| Pasos dentro del test | No | Sí (via `@allure.step`) |
| Screenshots | En la fila del test | En el paso donde falló |
| Historial entre ejecuciones | No | Sí (en CI) |
| Clasificación Epic/Feature/Story | No | Sí |
| Publicación en web | No (artifact descargable) | GitHub Pages |
| Requiere servidor externo | No | Sí (Java + Allure CLI) |
| Ideal para | Revisión rápida, portabilidad | Análisis profundo, reporting a stakeholders |

**Cuándo usar cada uno:**

- **pytest-html**: revisiones rápidas de CI, compartir con alguien que solo quiere abrir un archivo.
- **Allure**: demos, capacitaciones, reportes detallados con historial, ver exactamente en qué paso falló.

En este proyecto **se generan los dos simultáneamente** en cada ejecución.

---

## Prerequisitos

### Python: `allure-pytest`

Ya incluido en `requirements.txt`:

```
allure-pytest
```

Instalación:

```bash
pip install -r requirements.txt
```

### Java 8 o superior (para el CLI de Allure)

El CLI de Allure necesita Java para generar el HTML a partir de los JSON.

Verificar:

```bash
java -version
```

Si no está instalado: https://adoptium.net/ (recomendado: Temurin JDK 21)

### Allure CLI

**Windows (con Scoop):**

```powershell
scoop install allure
```

**Windows (con Chocolatey):**

```powershell
choco install allure
```

**macOS:**

```bash
brew install allure
```

Verificar instalación:

```bash
allure --version
```

> En CI (GitHub Actions) el CLI se instala automáticamente via la action `simple-elf/allure-report-action`.

---

## Integración en el proyecto

La integración usa cuatro archivos:

### 1. `requirements.txt`

```
allure-pytest
```

El paquete `allure-pytest` instala el plugin que se activa con `--alluredir` y habilita todos los decoradores.

### 2. `pytest.ini`

```ini
addopts = -v --tb=short --browser chromium --alluredir=allure-results
```

`--alluredir=allure-results` hace que cada ejecución genere automáticamente los archivos JSON intermedios en esa carpeta.

### 3. `pages/login_page.py`

Cada método público del Page Object está decorado con `@allure.step`:

```python
@allure.step("Navegar a la página de login")
def goto(self): ...

@allure.step("Ingresar credenciales: usuario={username}, contraseña={password}")
def login(self, username: str, password: str): ...

@allure.step("Verificar redirección al inventario tras login exitoso")
def assert_inventory_loaded(self) -> None: ...
```

Los templates `{param}` toman el valor real del argumento en el momento de ejecución.

### 4. `tests/test_login.py`

Cada test está decorado con metadatos de clasificación:

```python
@allure.epic("SauceDemo E2E")
@allure.feature("Login")
@allure.story("Login exitoso con usuario estándar")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Usuario estándar puede iniciar sesión y accede al inventario")
def test_valid_login(page):
    ...
```

### 5. `conftest.py`

En el hook `pytest_runtest_makereport`, cuando un test falla se adjunta el screenshot:

```python
allure.attach(
    png_bytes,
    name="Screenshot on failure",
    attachment_type=allure.attachment_type.PNG,
)
```

---

## Decoradores de Allure

### Jerarquía de clasificación

Allure organiza los tests en una jerarquía:

```
@allure.epic       →  nivel más alto (proyecto / sistema)
  @allure.feature  →  funcionalidad (ej: Login, Checkout)
    @allure.story  →  historia de usuario / escenario
```

Ejemplo en este proyecto:

```
SauceDemo E2E  (epic)
  └── Login  (feature)
        ├── Login exitoso con usuario estándar  (story)
        └── Manejo de errores en login  (story)
```

### `@allure.severity`

Indica la prioridad del test:

| Valor | Descripción |
|-------|-------------|
| `BLOCKER` | Impide el uso del sistema |
| `CRITICAL` | Funcionalidad principal |
| `NORMAL` | Comportamiento esperado estándar |
| `MINOR` | Problema menor |
| `TRIVIAL` | Cosmético o de baja prioridad |

### `@allure.title`

Nombre descriptivo que aparece en el reporte en lugar del nombre técnico de la función.

```python
@allure.title("Usuario estándar puede iniciar sesión y accede al inventario")
def test_valid_login(page): ...
```

### `@allure.step`

Decora métodos (generalmente del Page Object) para que aparezcan como pasos en el reporte:

```python
@allure.step("Navegar a la página de login")
def goto(self): ...
```

Los pasos se anidan automáticamente: si `login_as` llama a `login`, ambos aparecen como pasos, con `login` como hijo de `login_as`.

---

## Cómo funciona la generación del reporte

Allure trabaja en **dos pasos separados**:

```
Paso 1: pytest genera los datos
  pytest tests/ --alluredir=allure-results
  → crea archivos JSON en allure-results/
     ├── *-result.json     (resultado de cada test)
     ├── *-container.json  (fixtures/suites)
     └── *.png             (screenshots adjuntos)

Paso 2: Allure CLI genera el HTML
  allure serve allure-results   (servidor local, abre el browser)
  # o
  allure generate allure-results --clean -o allure-report
  allure open allure-report      (HTML estático generado)
```

Esta separación permite:
- Ejecutar tests en cualquier entorno (no necesita Java ni Allure CLI en la máquina que corre pytest).
- Transportar el directorio `allure-results/` y generar el reporte en otro entorno.

---

## Ejecución local

### Generar datos y ver reporte en el browser

```bash
# Paso 1: ejecutar tests
pytest tests/

# Paso 2: abrir reporte
allure serve allure-results
```

`allure serve` levanta un servidor HTTP local y abre el reporte automáticamente en el navegador.

### Generar HTML estático

```bash
allure generate allure-results --clean -o allure-report
allure open allure-report
```

Útil si querés compartir el reporte como carpeta.

### Solo con pytest-html (sin Allure CLI)

Si no tenés el CLI instalado, los datos JSON se generan igual (en `allure-results/`), pero no podés ver el reporte hasta instalar el CLI. Para ver algo en el browser, usá el reporte HTML:

```bash
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css
start reports/report.html
```

---

## Qué se ve en el reporte

Una vez abierto con `allure serve allure-results`:

### Vista Overview

- **Gráfico de dona**: distribución de resultados (passed/failed/broken).
- **Línea de tiempo**: cuándo corrió cada test en el tiempo.
- **Estadísticas**: total, pasados, fallidos.

### Vista Suites

```
SauceDemo E2E
  └── Login
        ├── Login exitoso con usuario estándar
        │     └── test_valid_login
        │           ├── [paso] Navegar a la página de login          0.8s
        │           ├── [paso] Iniciar sesión como usuario           0.4s
        │           │     └── [paso] Ingresar credenciales: ...      0.3s
        │           └── [paso] Verificar redirección al inventario   0.2s
        └── Manejo de errores en login
              ├── locked_user_cannot_log_in
              └── invalid_credentials_show_error
```

### En un test fallido

- Stack trace completo.
- Screenshot adjunto como attachment (si se configuró).
- Tiempos por paso para identificar cuál fue lento.

### Vista Behaviors

Organizado por Epic → Feature → Story. Útil para ver cobertura por funcionalidades de negocio.

---

## Allure en CI: GitHub Actions

El workflow `.github/workflows/e2e.yml` ejecuta tests y publica el reporte en GitHub Pages:

```yaml
- name: Run E2E tests (with Allure results)
  run: |
    pytest tests/ \
      --alluredir=allure-results \
      --html=reports/report.html \
      --self-contained-html \
      --css=reports/academy_report.css \
      -v --browser=chromium
  continue-on-error: true   # el reporte se genera aunque haya fallos

- name: Generate Allure HTML report
  uses: simple-elf/allure-report-action@v1
  if: always()
  with:
    allure_results: allure-results
    allure_report: allure-report
    allure_history: allure-history
    keep_reports: 20          # guarda historial de las últimas 20 ejecuciones

- name: Publish Allure report to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  if: always()
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_branch: gh-pages
    publish_dir: allure-report
```

Para activar GitHub Pages en tu repositorio:
1. Ir a **Settings → Pages**.
2. En **Source**, seleccionar la rama `gh-pages`.
3. El reporte queda disponible en `https://<usuario>.github.io/<repo>/`.

Ver [05 — CI/CD](05-CI_CD.md) para la explicación completa del workflow.

---

## Resumen de la integración

| Archivo | Cambio | Para qué |
|---------|--------|---------|
| `requirements.txt` | `allure-pytest` | Habilita el plugin |
| `pytest.ini` | `--alluredir=allure-results` | Genera datos en cada ejecución |
| `pages/login_page.py` | `@allure.step` en métodos | Pasos en el reporte |
| `tests/test_login.py` | `@allure.epic/feature/story/severity/title` | Clasificación y títulos |
| `conftest.py` | `allure.attach()` en fallo | Screenshots en el reporte |
| `e2e.yml` | steps de generación + Pages | Publicación automática |
