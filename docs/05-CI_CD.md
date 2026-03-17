# 05 — CI/CD: GitHub Actions

Este documento explica el pipeline de integración continua configurado en `.github/workflows/e2e.yml`: qué hace cada step, por qué está configurado así y cómo ver los resultados.

---

## Tabla de contenidos

1. [Cuándo se dispara el workflow](#cuándo-se-dispara-el-workflow)
2. [Permisos necesarios](#permisos-necesarios)
3. [Step a step: el pipeline completo](#step-a-step-el-pipeline-completo)
4. [Por qué `continue-on-error`](#por-qué-continue-on-error)
5. [Por qué `if: always()`](#por-qué-if-always)
6. [Cómo ver los reportes desde CI](#cómo-ver-los-reportes-desde-ci)
7. [GitHub Pages para Allure](#github-pages-para-allure)
8. [Diagrama del pipeline](#diagrama-del-pipeline)

---

## Cuándo se dispara el workflow

```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
```

El workflow corre en dos eventos:
- **Push a `main`/`master`**: cada vez que se hace un commit directo o se mergea un PR.
- **Pull Request hacia `main`/`master`**: corre automáticamente cuando se abre o actualiza un PR.

Esto garantiza que los tests corran antes de que el código llegue a la rama principal.

---

## Permisos necesarios

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

Estos permisos son requeridos por la action `peaceiris/actions-gh-pages` para publicar el reporte en la rama `gh-pages`:

- `contents: write`: necesario para hacer push a la rama `gh-pages`.
- `pages: write` + `id-token: write`: necesarios para GitHub Pages con tokens modernos.

---

## Step a step: el pipeline completo

### Step 1: Checkout

```yaml
- name: Checkout
  uses: actions/checkout@v4
```

Clona el repositorio en el runner de GitHub Actions. Sin esto, no hay código para ejecutar.

`@v4` es la versión major de la action. Se recomienda fijar versiones major para evitar cambios inesperados.

---

### Step 2: Set up Python

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

Instala Python 3.12 en el runner. Se especifica una versión concreta (no `latest`) para garantizar reproducibilidad entre ejecuciones.

---

### Step 3: Install dependencies

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

- Actualiza pip primero para evitar warnings.
- Instala todas las dependencias de `requirements.txt`: pytest, playwright, pytest-html, allure-pytest, etc.

---

### Step 4: Install Playwright browsers

```yaml
- name: Install Playwright browsers
  run: playwright install chromium --with-deps
```

Los browsers de Playwright no se instalan con `pip`: hay que instalarlos por separado con el CLI.

- `chromium`: solo instala Chromium (no Firefox ni WebKit), para acelerar el step.
- `--with-deps`: instala también las dependencias del sistema operativo necesarias para que el browser funcione en Linux (el runner es Ubuntu).

---

### Step 5: Run E2E tests

```yaml
- name: Run E2E tests (with Allure results)
  run: |
    pytest tests/ \
      --alluredir=allure-results \
      --html=reports/report.html \
      --self-contained-html \
      --css=reports/academy_report.css \
      -v \
      --browser=chromium
  continue-on-error: true
```

Ejecuta toda la suite con ambos reportes activos simultáneamente:

| Flag | Propósito |
|------|-----------|
| `--alluredir=allure-results` | Genera JSON para Allure en esa carpeta |
| `--html=reports/report.html` | Genera reporte HTML de pytest-html |
| `--self-contained-html` | HTML portable (sin assets externos) |
| `--css=reports/academy_report.css` | Aplica el tema visual Academy |
| `-v` | Output detallado en el log del workflow |
| `--browser=chromium` | Usa Chromium como browser |

`continue-on-error: true` — ver sección siguiente.

---

### Step 6: Upload allure-results artifact

```yaml
- name: Upload allure-results artifact
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: allure-results
    path: allure-results/
    retention-days: 30
```

Sube la carpeta `allure-results/` como artifact descargable desde la UI de GitHub Actions. Útil si la publicación en Pages falla o si se quiere regenerar el reporte localmente.

`retention-days: 30` — el artifact se borra automáticamente después de 30 días.

---

### Step 7: Upload HTML report artifact

```yaml
- name: Upload HTML report artifact
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: e2e-html-report
    path: reports/report.html
    retention-days: 30
```

Sube el reporte HTML de pytest-html. Es descargable directamente y abre en el navegador sin servidor.

---

### Step 8: Generate Allure HTML report

```yaml
- name: Generate Allure HTML report
  uses: simple-elf/allure-report-action@v1
  if: always()
  with:
    allure_results: allure-results
    allure_report: allure-report
    allure_history: allure-history
    keep_reports: 20
```

La action `simple-elf/allure-report-action` instala el CLI de Allure automáticamente (con Java incluido) y genera el HTML a partir de los JSON.

- `allure_results`: directorio con los JSON generados por pytest.
- `allure_report`: directorio donde se genera el HTML.
- `allure_history`: directorio con el historial de ejecuciones anteriores.
- `keep_reports: 20`: guarda el historial de las últimas 20 ejecuciones. Aparece como gráfico de tendencia en el Overview de Allure.

---

### Step 9: Publish Allure report to GitHub Pages

```yaml
- name: Publish Allure report to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  if: always()
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_branch: gh-pages
    publish_dir: allure-report
```

Hace push del contenido de `allure-report/` a la rama `gh-pages` del repositorio.

GitHub Pages sirve automáticamente el contenido de esa rama como un sitio estático.

- `github_token`: token autogenerado por GitHub Actions. No requiere configuración manual.
- `publish_branch: gh-pages`: la rama donde se publica. Si no existe, la crea.
- `publish_dir: allure-report`: el directorio que se publica.

---

## Por qué `continue-on-error`

```yaml
  continue-on-error: true
```

Sin esta línea, si algún test falla, el step de pytest devuelve exit code 1, lo que marca todo el job como fallido y **cancela** los steps siguientes (los de publicación del reporte).

Con `continue-on-error: true`:
- Si los tests fallan, el step se marca como "failed" pero el job **continúa**.
- Los steps de artifact y Pages se ejecutan de todos modos.
- El job en sí también puede marcarse como fallido en el final (vía el propio pytest exit code), pero los reportes ya están publicados.

Esto es esencial: **el reporte es más valioso cuando hay fallos**, que es exactamente cuando queremos verlo.

---

## Por qué `if: always()`

```yaml
  if: always()
```

La condición `always()` en GitHub Actions hace que el step corra **sin importar el resultado de los steps anteriores**.

Si no se especifica `if: always()` y el step de pytest falla (tests fallidos), los steps siguientes no correrían aunque tengan `continue-on-error: true` en el step anterior.

Combinando ambos:
- `continue-on-error: true` en el step de pytest → el job no se cancela.
- `if: always()` en los steps de reporte → corren sin importar el estado anterior.

---

## Cómo ver los reportes desde CI

### Reporte HTML (pytest-html)

1. Ir al repositorio en GitHub.
2. Clic en la pestaña **Actions**.
3. Clic en la ejecución deseada.
4. En la sección **Artifacts** al final de la página, descargar **e2e-html-report**.
5. Descomprimir el ZIP y abrir `report.html` en el navegador.

### Reporte Allure (GitHub Pages)

1. Una vez configurado GitHub Pages, la URL es: `https://<usuario>.github.io/<nombre-del-repo>/`.
2. Cada push actualiza automáticamente el reporte publicado.

### Datos crudos de Allure (artifact)

1. En la sección **Artifacts**, descargar **allure-results**.
2. Descomprimir y ejecutar localmente: `allure serve allure-results`.

---

## GitHub Pages para Allure

Para activar GitHub Pages en el repositorio:

1. Ir a **Settings** del repositorio.
2. En el menú izquierdo, clic en **Pages**.
3. En **Source**, seleccionar **Deploy from a branch**.
4. En **Branch**, seleccionar `gh-pages` y `/root`.
5. Guardar.

A partir del siguiente push, el reporte Allure estará disponible en:

```
https://<tu-usuario>.github.io/<nombre-del-repo>/
```

---

## Referencia de GitHub Actions usadas

Cada `uses:` en el YAML apunta a una action específica de GitHub Actions Marketplace. Esta tabla explica qué es cada una, quién la mantiene y por qué se usa.

| Action | Versión | Mantenida por | Qué hace en este workflow |
|--------|---------|--------------|--------------------------|
| `actions/checkout` | `@v4` | GitHub (oficial) | Clona el repositorio en el runner |
| `actions/setup-python` | `@v5` | GitHub (oficial) | Instala Python 3.12 y configura el entorno |
| `actions/upload-artifact` | `@v4` | GitHub (oficial) | Sube archivos como artifacts descargables |
| `simple-elf/allure-report-action` | `@v1` | Comunidad | Instala Java + Allure CLI y genera el HTML desde los JSON |
| `peaceiris/actions-gh-pages` | `@v4` | Comunidad | Hace push de una carpeta a la rama `gh-pages` para publicar en GitHub Pages |

### `actions/checkout@v4`

```yaml
- uses: actions/checkout@v4
```

Action oficial de GitHub. Sin ella el runner tiene un filesystem vacío. Clona el repo con profundidad mínima por defecto (`fetch-depth: 1`) para que sea rápido.

### `actions/setup-python@v5`

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
```

Action oficial de GitHub. Instala la versión de Python especificada, configura el PATH y habilita cache de pip si se configura. Se usa `"3.12"` (no `"3"` ni `"latest"`) para garantizar que la ejecución sea reproducible entre runs.

### `actions/upload-artifact@v4`

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: allure-results
    path: allure-results/
    retention-days: 30
```

Action oficial de GitHub. Sube archivos o carpetas como artifacts del run. Aparecen en la sección **Artifacts** al final de la página del workflow run. Con `if: always()` el artifact se sube incluso si los tests fallan. `retention-days: 30` los borra automáticamente.

### `simple-elf/allure-report-action@v1`

```yaml
- uses: simple-elf/allure-report-action@v1
  if: always()
  with:
    allure_results: allure-results
    allure_report: allure-report
    allure_history: allure-history
    keep_reports: 20
```

Action de la comunidad. Internamente:
1. Descarga e instala el CLI de Allure (con Java incluido).
2. Lee el historial de ejecuciones anteriores (`allure_history`) para generar el gráfico de tendencias.
3. Corre `allure generate allure-results -o allure-report`.
4. Guarda los datos de esta ejecución en `allure_history` para el próximo run.

`keep_reports: 20` controla cuántas ejecuciones históricas se mantienen en el gráfico de tendencias del Overview.

### `peaceiris/actions-gh-pages@v4`

```yaml
- uses: peaceiris/actions-gh-pages@v4
  if: always()
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_branch: gh-pages
    publish_dir: allure-report
```

Action de la comunidad, ampliamente usada. Hace git push del contenido de `publish_dir` a la rama `publish_branch`. Si la rama no existe la crea. El `GITHUB_TOKEN` es un token autogenerado por GitHub para cada run del workflow; no requiere configuración manual en Secrets.

---

## Diagrama del pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Trigger: push o PR a main/master                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                  ┌─────────▼──────────┐
                  │  checkout          │
                  └─────────┬──────────┘
                            │
                  ┌─────────▼──────────┐
                  │  setup python 3.12 │
                  └─────────┬──────────┘
                            │
                  ┌─────────▼──────────┐
                  │  pip install -r    │
                  │  requirements.txt  │
                  └─────────┬──────────┘
                            │
                  ┌─────────▼──────────┐
                  │  playwright install│
                  │  chromium          │
                  └─────────┬──────────┘
                            │
                  ┌─────────▼──────────────────────┐
                  │  pytest tests/                  │
                  │  --alluredir=allure-results      │
                  │  --html=reports/report.html      │
                  │  continue-on-error: true         │
                  └─────────┬──────────────────────┘
                            │ (siempre continúa)
            ┌───────────────┼───────────────┐
            │               │               │
  ┌─────────▼──────┐ ┌──────▼──────┐ ┌─────▼───────────────┐
  │ upload artifact│ │ upload HTML │ │ allure-report-action │
  │ allure-results │ │ report.html │ │ (genera HTML+history)│
  └────────────────┘ └─────────────┘ └─────────┬────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │ gh-pages action      │
                                    │ publica en Pages     │
                                    └─────────────────────┘
```
