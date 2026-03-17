# Cómo funciona el reporte HTML personalizado

Este documento explica cómo está construido y configurado el reporte HTML que genera el proyecto al ejecutar los tests.

---

## Tabla de contenidos

1. [Tecnología base: pytest-html](#tecnología-base-pytest-html)
2. [Piezas que componen el reporte](#piezas-que-componen-el-reporte)
3. [El archivo CSS: `academy_report.css`](#el-archivo-css-academy_reportcss)
4. [El archivo `conftest.py`: lógica del reporte](#el-archivo-conftestpy-lógica-del-reporte)
5. [Cómo se genera en CI: `e2e.yml`](#cómo-se-genera-en-ci-e2eyml)
6. [Cómo generar el reporte localmente](#cómo-generar-el-reporte-localmente)
7. [Diagrama de flujo](#diagrama-de-flujo)

---

## Tecnología base: pytest-html

El reporte es generado por el plugin **[pytest-html](https://pytest-html.readthedocs.io/)**.  
Este plugin se activa pasando el flag `--html` al ejecutar pytest:

```bash
pytest --html=reports/report.html --self-contained-html
```

| Flag | Descripción |
|---|---|
| `--html=reports/report.html` | Ruta donde se guarda el archivo HTML generado |
| `--self-contained-html` | Incrusta todos los assets (JS, CSS base) dentro del HTML, sin dependencias externas |
| `--css=reports/academy_report.css` | Inyecta el CSS personalizado encima del estilo por defecto |

El resultado es un **único archivo `.html` portable** que se puede abrir en cualquier navegador sin necesidad de servidor.

---

## Piezas que componen el reporte

El reporte está formado por tres piezas que trabajan juntas:

```
pytest-html (plugin)          → genera la estructura base del HTML
academy_report.css            → sobreescribe el estilo visual (tema oscuro)
conftest.py (hooks)           → inyecta contenido dinámico (dashboard, banner, screenshots)
```

### Archivo `reports/report.html`

Es el archivo generado automáticamente. **No se edita a mano**, se produce cada vez que se ejecutan los tests. Contiene:

- Título del reporte
- Tabla de metadatos del entorno
- Dashboard de tarjetas con totales
- Banner informativo
- Tabla de resultados de cada test
- Screenshots incrustados en base64 en los tests que fallaron

---

## El archivo CSS: `academy_report.css`

Ubicado en `reports/academy_report.css`, sobreescribe el estilo por defecto de pytest-html para aplicar un **tema oscuro personalizado** con la identidad visual del proyecto.

### Paleta de colores (variables CSS)

```css
:root {
  --bg: #0f1419;          /* fondo principal */
  --surface: #1a2332;     /* fondo de cards y tablas */
  --surface2: #243044;    /* fondo de encabezados */
  --text: #e8edf4;        /* texto principal */
  --muted: #8b9cb3;       /* texto secundario */
  --accent: #c9a227;      /* dorado: títulos, links, hover */
  --pass: #3d9a6e;        /* verde: tests pasados */
  --fail: #e85d5d;        /* rojo: tests fallidos */
  --skip: #d4a03c;        /* amarillo: tests saltados */
}
```

### Tipografía

Se importan dos fuentes de Google Fonts:

| Fuente | Uso |
|---|---|
| **Instrument Serif** | Título `<h1>` del reporte (elegante, serif) |
| **DM Sans** | Cuerpo de texto, tablas, labels (limpia, sans-serif) |

### Componentes visuales definidos en el CSS

| Clase CSS | Descripción |
|---|---|
| `.academy-dashboard` | Grid de 5 tarjetas con los totales |
| `.academy-card` | Tarjeta individual del dashboard |
| `.academy-card--pass/fail/skip/total` | Variante de color por estado |
| `.academy-card__value` | Número grande en cada tarjeta |
| `.academy-card__label` | Etiqueta debajo del número |
| `.academy-banner` | Franja informativa con degradado |
| `#environment` | Tabla de metadatos del entorno |
| `.log` | Bloque de logs con fondo oscuro |

---

## El archivo `conftest.py`: lógica del reporte

El archivo `conftest.py` en la raíz del proyecto contiene los **hooks de pytest** que enriquecen el reporte con contenido dinámico. Estos hooks son funciones especiales que pytest llama automáticamente en momentos específicos de la ejecución.

### Hook 1: `pytest_html_report_title`

```python
def pytest_html_report_title(report) -> None:
    report.title = "Academy E2E — Test Report"
```

**Qué hace:** Cambia el título que aparece en el `<title>` del HTML y en el encabezado `<h1>` del reporte.  
**Sin este hook:** el título sería la ruta del archivo (ej: `reports/report.html`).

---

### Hook 2: `pytest_configure`

```python
@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    ...
    meta["Project"] = "Academy E2E Automation"
    meta["Target app"] = "SauceDemo"
    meta["BASE_URL"] = BASE_URL
    meta["Stack"] = "Python · pytest · Playwright · POM"
```

**Qué hace:** Agrega filas extra a la tabla **Environment** que aparece al inicio del reporte.  
**Cuándo corre:** Durante la configuración inicial de pytest, antes de que arranquen los tests.  
**`trylast=True`:** Garantiza que este hook corre después de que pytest-metadata ya inicializó el diccionario de metadatos.  
**Guardado:** Solo agrega metadatos si se está generando un reporte HTML (verifica `--htmlpath`).

---

### Hook 3: `pytest_html_results_summary`

```python
def pytest_html_results_summary(prefix, summary, postfix, session) -> None:
    ...
    prefix.insert(0, banner + dash)
```

**Qué hace:** Inyecta HTML personalizado **antes** de la tabla de resultados. Inserta dos elementos:

1. **Banner** — franja con texto informativo sobre el reporte.
2. **Dashboard** — 5 tarjetas con los contadores: Total, Passed, Failed/Error, Skipped, Duration.

**Cómo obtiene los datos:** Lee las estadísticas del `terminalreporter` (el plugin que muestra resultados en consola), que ya tiene los conteos actualizados al finalizar todos los tests.

**Los tres parámetros `prefix/summary/postfix`** son listas de strings HTML que se renderizan en orden:
- `prefix` → va antes del resumen estándar
- `summary` → es el resumen estándar de pytest-html
- `postfix` → va después

---

### Hook 4: `pytest_runtest_makereport`

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    page = item.funcargs.get("page")
    ...
    png_bytes = page.screenshot(full_page=False)
    extra = html_extras.png(png_bytes, "Screenshot on failure")
    rep.extra = getattr(rep, "extra", []) + [extra]
```

**Qué hace:** Captura automáticamente un screenshot del navegador cuando un test falla y lo adjunta al reporte.

**Cómo funciona paso a paso:**

| Paso | Descripción |
|---|---|
| `hookwrapper=True` | Permite ejecutar código tanto antes como después del hook original |
| `outcome = yield` | Pausa y deja que pytest genere el resultado del test |
| `rep = outcome.get_result()` | Obtiene el objeto con el resultado (passed/failed/etc.) |
| `rep.when != "call"` | Solo actúa en la fase de ejecución del test (no en setup ni teardown) |
| `item.funcargs.get("page")` | Obtiene el objeto `page` de Playwright de los fixtures del test |
| `page.screenshot()` | Toma la captura de pantalla como bytes PNG |
| `html_extras.png(...)` | Convierte los bytes en un extra embebido en base64 |
| `rep.extra` | Lista donde pytest-html busca el contenido extra de cada fila |

**El screenshot aparece** en la columna **Links** de la tabla de resultados, en la fila del test fallido. Al hacer clic, se expande la imagen directamente en el HTML.

---

### Hooks 5 y 6: `pytest_sessionstart` / `pytest_sessionfinish`

```python
def pytest_sessionstart(session: pytest.Session) -> None:
    session._starttime = time.time()

def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    session._sessionduration = time.time() - getattr(session, "_starttime", time.time())
```

**Qué hacen:** Miden el tiempo total de ejecución de toda la suite.  
- `pytest_sessionstart` guarda el timestamp al inicio.  
- `pytest_sessionfinish` calcula la diferencia al final.  
- El valor calculado (`_sessionduration`) es leído por el hook `pytest_html_results_summary` para mostrar la tarjeta **Duration** en el dashboard.

---

## Cómo se genera en CI: `e2e.yml`

El workflow de GitHub Actions en `.github/workflows/e2e.yml` genera el reporte automáticamente en cada push o pull request:

```yaml
- name: Run E2E tests
  run: |
    pytest tests/ \
      --html=reports/report.html \
      --self-contained-html \
      --css=reports/academy_report.css \
      -v \
      --browser=chromium

- name: Upload HTML report
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: e2e-report
    path: reports/report.html
    retention-days: 30
```

### Puntos clave del workflow

| Elemento | Por qué está así |
|---|---|
| `--self-contained-html` | El artifact es un único archivo sin dependencias, descargable y abrile sin servidor |
| `--css=reports/academy_report.css` | Aplica el tema oscuro personalizado |
| `if: always()` | El artifact se sube **aunque los tests fallen**, para poder revisar qué falló |
| `retention-days: 30` | El artifact se conserva 30 días en GitHub antes de borrarse automáticamente |

### Cómo descargar el reporte desde GitHub Actions

1. Ir al repositorio en GitHub.
2. Clic en la pestaña **Actions**.
3. Clic en la ejecución del workflow deseada.
4. En la sección **Artifacts** al final de la página, descargar **e2e-report**.
5. Descomprimir el ZIP y abrir `report.html` en el navegador.

---

## Cómo generar el reporte localmente

```bash
pytest tests/ \
  --html=reports/report.html \
  --self-contained-html \
  --css=reports/academy_report.css \
  -v
```

O simplemente ejecutar `pytest` sin flags si `pytest.ini` ya los tiene configurados en `addopts`.

Luego abrir el archivo generado:

```bash
# Windows
start reports/report.html

# macOS
open reports/report.html

# Linux
xdg-open reports/report.html
```

---

## Diagrama de flujo

```
pytest run
    │
    ├── pytest_sessionstart()        → guarda timestamp de inicio
    │
    ├── [para cada test]
    │     ├── setup (fixture `page` crea browser)
    │     ├── call  (ejecuta el test)
    │     │     └── pytest_runtest_makereport()
    │     │           └── si FALLA: screenshot → rep.extra
    │     └── teardown
    │
    ├── pytest_sessionfinish()       → calcula duración total
    │
    └── pytest-html genera report.html
          ├── pytest_html_report_title()       → título personalizado
          ├── pytest_configure()               → metadatos del entorno
          ├── pytest_html_results_summary()    → banner + dashboard de tarjetas
          ├── academy_report.css               → tema oscuro (inyectado con --css)
          └── screenshots (base64 en extras)   → adjuntos en filas de tests fallidos
```

---

## Resumen rápido

| Componente | Archivo | Qué aporta al reporte |
|---|---|---|
| Generador base | `pytest-html` (dependencia) | Estructura HTML del reporte |
| Estilos | `reports/academy_report.css` | Tema oscuro, tipografía, colores de estado |
| Título | `conftest.py` hook 1 | Nombre personalizado en el `<h1>` |
| Metadatos | `conftest.py` hook 2 | Tabla Environment con info del proyecto |
| Dashboard | `conftest.py` hook 3 | Tarjetas con totales y duración |
| Screenshots | `conftest.py` hook 4 | Imágenes adjuntas en tests fallidos (pytest-html + Allure) |
| Duración | `conftest.py` hooks 5-6 | Tiempo total medido de la sesión |
| CI/CD | `.github/workflows/e2e.yml` | Generación y publicación como artifact |

---

## pytest-html vs Allure: cuándo usar cada uno

Este proyecto genera **ambos reportes simultáneamente** en cada ejecución. Cada uno tiene un propósito diferente:

| Característica | pytest-html | Allure |
|----------------|------------|--------|
| Formato | Un solo `.html` portable | Carpeta JSON + HTML generado |
| Pasos dentro del test | No | Sí (via `@allure.step`) |
| Screenshots | En la columna Links de la fila | En el paso donde ocurrió el fallo |
| Historial entre ejecuciones | No | Sí (en CI con GitHub Pages) |
| Clasificación Epic/Feature/Story | No | Sí |
| Requiere servidor/Java | No | Sí (Allure CLI) |
| Ideal para | Revisión rápida, compartir como archivo | Análisis profundo, demos, reporting |

### Usar pytest-html cuando:
- Querés abrir el reporte sin instalar nada extra.
- Lo compartís como attachment en un email o Slack.
- Necesitás ver rápidamente si los tests pasaron o fallaron.

### Usar Allure cuando:
- Necesitás ver exactamente en qué paso del test ocurrió el fallo.
- Querés ver el historial de ejecuciones anteriores.
- Estás haciendo una demo o presentación del proyecto.
- Los stakeholders necesitan ver cobertura por Feature/Story.

---

## Documentación relacionada

| Documento | Enlace |
|-----------|--------|
| Allure Report — integración completa | [`docs/04-ALLURE_REPORT.md`](../docs/04-ALLURE_REPORT.md) |
| conftest.py y hooks explicados | [`docs/03-CONFTEST_AND_HOOKS.md`](../docs/03-CONFTEST_AND_HOOKS.md) |
| CI/CD y publicación en GitHub Pages | [`docs/05-CI_CD.md`](../docs/05-CI_CD.md) |
| Ejercicios: personalizar el CSS | [`docs/exercises/01-CUSTOMIZE_REPORT_CSS.md`](../docs/exercises/01-CUSTOMIZE_REPORT_CSS.md) |
| Ejercicios: correr los reportes | [`docs/exercises/02-RUNNING_REPORTS.md`](../docs/exercises/02-RUNNING_REPORTS.md) |
