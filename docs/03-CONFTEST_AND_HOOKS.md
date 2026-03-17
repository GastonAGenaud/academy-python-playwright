# 03 — conftest.py y hooks de pytest

Este documento explica qué es `conftest.py`, cómo funciona el sistema de hooks de pytest y el detalle de cada uno de los 6 hooks implementados en este proyecto.

---

## Tabla de contenidos

1. [¿Qué es conftest.py?](#qué-es-conftestpy)
2. [¿Qué son los hooks de pytest?](#qué-son-los-hooks-de-pytest)
3. [Conceptos clave: hookwrapper y trylast](#conceptos-clave-hookwrapper-y-trylast)
4. [Resumen de hooks implementados](#resumen-de-hooks-implementados)
5. [Hook 1: pytest_html_report_title](#hook-1-pytest_html_report_title)
6. [Hook 2: pytest_configure](#hook-2-pytest_configure)
7. [Hook 3: pytest_html_results_summary](#hook-3-pytest_html_results_summary)
8. [Hook 4: pytest_runtest_makereport](#hook-4-pytest_runtest_makereport)
9. [Hook 5: pytest_sessionstart](#hook-5-pytest_sessionstart)
10. [Hook 6: pytest_sessionfinish](#hook-6-pytest_sessionfinish)
11. [Flujo de datos entre hooks](#flujo-de-datos-entre-hooks)

---

## ¿Qué es conftest.py?

`conftest.py` es un archivo especial de pytest que se carga **automáticamente** antes de ejecutar cualquier test. No hay que importarlo: pytest lo descubre solo.

Características:
- Puede vivir en la raíz del proyecto (afecta a toda la suite) o en subcarpetas (afecta solo a esa carpeta y sus subdirectorios).
- Es el lugar estándar para definir **fixtures** y **hooks**.
- Múltiples conftest.py pueden coexistir en distintos niveles.

En este proyecto hay un solo `conftest.py` en la raíz, que registra hooks para enriquecer los reportes HTML y Allure.

---

## ¿Qué son los hooks de pytest?

Los hooks son **funciones con nombres especiales** que pytest llama automáticamente en momentos específicos del ciclo de vida de la ejecución.

Pytest define qué hooks existen (su nombre, parámetros y cuándo se llaman). El desarrollador implementa los que necesita en `conftest.py`.

```
pytest lifecycle
   │
   ├── pytest_sessionstart       → inicio de sesión
   ├── pytest_configure          → configuración inicial
   ├── [colección de tests]
   ├── [para cada test]
   │     ├── pytest_runtest_setup
   │     ├── pytest_runtest_call
   │     └── pytest_runtest_makereport   → resultado de cada fase
   ├── [generación del reporte HTML]
   │     ├── pytest_html_report_title
   │     └── pytest_html_results_summary
   └── pytest_sessionfinish      → fin de sesión
```

---

## Conceptos clave: hookwrapper y trylast

### `@pytest.hookimpl(hookwrapper=True)`

Por defecto, un hook reemplaza o complementa el comportamiento estándar. Con `hookwrapper=True`, el hook **envuelve** al hook original:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield   # ← aquí se ejecuta el hook original (y todos los demás)
    rep = outcome.get_result()
    # código que corre DESPUÉS del hook original
```

El `yield` divide el hook en dos partes:
- Todo lo que está **antes** del `yield` corre antes del hook original.
- Todo lo que está **después** del `yield` corre después.

Esto permite capturar el resultado (`outcome`) y modificarlo o actuar en base a él.

### `@pytest.hookimpl(trylast=True)`

Cuando múltiples plugins implementan el mismo hook, pytest los llama en un orden. `trylast=True` garantiza que este hook corre **después** de todos los demás.

Se usa en `pytest_configure` para asegurarse de que `pytest-metadata` ya inicializó el diccionario de metadatos antes de que intentemos agregarle entradas.

---

## Resumen de hooks implementados

| Hook | Tipo | Cuándo corre | Qué hace |
|------|------|-------------|---------|
| `pytest_html_report_title` | Normal | Al generar el HTML | Cambia el `<h1>` del reporte |
| `pytest_configure` | `trylast` | Antes de los tests | Agrega filas a la tabla Environment |
| `pytest_html_results_summary` | Normal | Al generar el HTML | Inserta banner + dashboard de tarjetas |
| `pytest_runtest_makereport` | `hookwrapper` | Después de cada fase del test | Captura screenshot en fallos |
| `pytest_sessionstart` | Normal | Al iniciar la sesión | Guarda timestamp de inicio |
| `pytest_sessionfinish` | Normal | Al terminar la sesión | Calcula duración total |

---

## Hook 1: pytest_html_report_title

```python
def pytest_html_report_title(report) -> None:
    report.title = "Academy E2E — Test Report"
```

**Cuándo corre:** cuando pytest-html está a punto de escribir el `<title>` y `<h1>` del HTML.

**Qué cambia:** sin este hook, el título sería la ruta del archivo de salida (ej: `reports/report.html`). Con el hook, el título es legible y tiene identidad del proyecto.

**Parámetro `report`:** objeto de pytest-html con la propiedad `title` que se puede asignar.

---

## Hook 2: pytest_configure

```python
@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
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
```

**Cuándo corre:** durante la configuración inicial de pytest, antes de que arranquen los tests.

**`trylast=True`:** garantiza que pytest-metadata ya inicializó `config.stash[metadata_key]` antes de que intentemos accederlo.

**`config.getoption("htmlpath", default=None)`:** solo agrega metadatos si se está generando un reporte HTML. Si se corre `pytest` sin `--html`, este hook no hace nada.

**`config.stash[metadata_key]`:** el diccionario de metadatos que gestiona `pytest-metadata`. Cada clave/valor agrega una fila a la tabla **Environment** del reporte.

**`try/except`:** si `pytest-metadata` no está instalado o no está inicializado aún, falla silenciosamente. El reporte se genera igual, simplemente sin estas filas extra.

**Resultado en el reporte:**

```
Environment
─────────────────────────────────────
Python          3.13.5
Platform        Windows-11-...
Project         Academy E2E Automation
Target app      SauceDemo
BASE_URL        https://www.saucedemo.com/
Stack           Python · pytest · Playwright · POM
```

---

## Hook 3: pytest_html_results_summary

```python
def pytest_html_results_summary(prefix, summary, postfix, session) -> None:
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

    banner = '<div class="academy-banner">...'
    dash = '<div class="academy-dashboard">...'
    prefix.insert(0, banner + dash)
```

**Cuándo corre:** cuando pytest-html está construyendo la sección de resumen del HTML.

**Parámetros `prefix`, `summary`, `postfix`:** son listas de strings HTML. Se renderizan en orden:
- `prefix` → antes del resumen estándar de pytest-html
- `summary` → resumen estándar (pasa/falla/skipped)
- `postfix` → después

Hacer `prefix.insert(0, ...)` agrega el HTML al principio de la sección.

**Cómo obtiene los conteos:**

```python
tr = session.config.pluginmanager.get_plugin("terminalreporter")
passed = len(tr.stats.get("passed", []))
```

El `terminalreporter` es el plugin que muestra el output en la terminal (los puntos y letras). Mantiene un diccionario `stats` con una lista de resultados por categoría. Al finalizar todos los tests, esta información ya está disponible.

**Cómo obtiene la duración:**

Usa el valor calculado por `pytest_sessionfinish` (hook 6), que se guarda en `session._sessionduration`. Si por algún motivo no está disponible, calcula desde `session._starttime` (hook 5).

**Resultado en el reporte:** un banner informativo y 5 tarjetas visuales (Total, Passed, Failed/Error, Skipped, Duration) arriba de la tabla de resultados.

---

## Hook 4: pytest_runtest_makereport

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
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

    # Adjuntar en Allure
    allure.attach(
        png_bytes,
        name="Screenshot on failure",
        attachment_type=allure.attachment_type.PNG,
    )

    # Adjuntar en pytest-html
    try:
        import pytest_html.extras as html_extras
        extra = html_extras.png(png_bytes, "Screenshot on failure")
        rep.extra = getattr(rep, "extra", []) + [extra]
    except ImportError:
        pass
```

Este es el hook más complejo. Paso a paso:

**`@pytest.hookimpl(hookwrapper=True)`:** permite ejecutar código después de que pytest genera el resultado del test.

**`outcome = yield`:** pausa el hook y deja que pytest (y otros plugins) generen el `TestReport`. Cuando el yield retorna, `outcome` contiene ese resultado.

**`rep = outcome.get_result()`:** obtiene el objeto `TestReport` con toda la información del resultado.

**`rep.when != "call"`:** cada test tiene 3 fases: `setup`, `call` y `teardown`. Solo nos interesa la fase `call`, que es la ejecución real del test. En `setup` y `teardown` no queremos tomar screenshots.

**`not rep.failed`:** solo actúa si el test falló. No hay razón para tomar screenshots de tests que pasaron.

**`item.funcargs.get("page")`:** `item.funcargs` es el diccionario de argumentos (fixtures) del test. Si el test recibe el fixture `page` de `pytest-playwright`, está aquí. Si no (ej: test sin browser), retorna `None` y el hook no hace nada.

**`page.screenshot(full_page=False)`:** toma una captura de la ventana visible (no toda la página), en bytes PNG.

**Adjuntar en Allure:** `allure.attach()` guarda el PNG en los archivos de resultados de Allure. Aparece como attachment en el test fallido.

**Adjuntar en pytest-html:** `html_extras.png()` convierte los bytes a un extra incrustado en base64. Al asignarlo a `rep.extra`, pytest-html lo renderiza como imagen en la columna **Links** de la fila del test fallido.

---

## Hook 5: pytest_sessionstart

```python
def pytest_sessionstart(session: pytest.Session) -> None:
    session._starttime = time.time()
```

**Cuándo corre:** exactamente al inicio de la sesión pytest, antes de cualquier test.

**Qué hace:** guarda el timestamp UNIX actual en el objeto `session`. Este objeto persiste durante toda la ejecución, por lo que está disponible para otros hooks.

**Por qué custom y no el tiempo de pytest:** pytest tiene su propio registro de tiempo, pero no está expuesto fácilmente para uso en hooks de reporte. Este approach simple y explícito es más confiable.

---

## Hook 6: pytest_sessionfinish

```python
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    session._sessionduration = time.time() - getattr(session, "_starttime", time.time())
```

**Cuándo corre:** al terminar todos los tests, antes de que se generen los reportes.

**Qué hace:** calcula la duración restando el timestamp guardado en `pytest_sessionstart` del tiempo actual. Guarda el resultado en `session._sessionduration`.

**`getattr(session, "_starttime", time.time())`:** fallback por si `pytest_sessionstart` no corrió por algún motivo (duración = 0).

**Cuándo se usa:** el hook `pytest_html_results_summary` lee `session._sessionduration` para mostrar la tarjeta **Duration** en el dashboard.

---

## Flujo de datos entre hooks

```
pytest_sessionstart
  └── guarda session._starttime
         │
         ▼
[todos los tests corren]
         │
         ├── pytest_runtest_makereport (por cada test)
         │     └── si falla: screenshot → allure.attach() + rep.extra
         │
         ▼
pytest_sessionfinish
  └── calcula session._sessionduration = now - _starttime
         │
         ▼
[pytest-html genera el HTML]
         │
         ├── pytest_html_report_title
         │     └── report.title = "Academy E2E — Test Report"
         │
         ├── pytest_configure (trylast, corre antes del HTML)
         │     └── config.stash[metadata_key]["Project"] = ...
         │
         └── pytest_html_results_summary
               ├── lee terminalreporter.stats → conteos
               ├── lee session._sessionduration → duración
               └── prefix.insert(0, banner + dashboard)
```

La clave es que `pytest_sessionfinish` corre **antes** de que pytest-html renderice el HTML, por lo que `_sessionduration` ya está disponible cuando `pytest_html_results_summary` lo necesita.
