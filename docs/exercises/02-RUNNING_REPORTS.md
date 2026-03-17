# Ejercicio 02 — Correr los reportes

En este ejercicio vas a ejecutar los tests con distintas combinaciones de flags y reportes, observar las diferencias entre pytest-html y Allure, y practicar forzar un fallo para ver cómo aparecen los screenshots.

---

## Prerequisitos

- `pip install -r requirements.txt` ejecutado.
- Allure CLI instalado (solo para los ejercicios con Allure): ver [04-ALLURE_REPORT.md](../04-ALLURE_REPORT.md#prerequisitos).

---

## Ejercicio 1: Generar el reporte HTML y leer el dashboard

### Objetivo

Generar el reporte HTML y verificar que el dashboard muestra los conteos correctos.

### Pasos

1. Ejecutar todos los tests con reporte HTML:

```bash
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css
```

2. Abrir el reporte:

```powershell
# Windows
start reports/report.html
```

```bash
# macOS
open reports/report.html

# Linux
xdg-open reports/report.html
```

3. Observar:
   - El título del reporte en el `<h1>`.
   - La tabla **Environment** con los metadatos del proyecto.
   - Las tarjetas del dashboard: Total, Passed, Failed/Error, Skipped, Duration.
   - La tabla de tests con las columnas Result, Test, Duration, Links.

### Preguntas para responder

- ¿Qué valor muestra la tarjeta **Total**?
- ¿Cuántos tests pasaron?
- ¿Cuál fue la duración total de la suite?
- ¿Qué metadata se ve en la tabla Environment?

---

## Ejercicio 2: Forzar un fallo y ver el screenshot

### Objetivo

Introducir un fallo intencional en un test, regenerar el reporte y verificar que aparece el screenshot en el reporte HTML y en Allure.

### Pasos

1. Abrir `data/users.py` y cambiar la contraseña de `STANDARD_USER` por una inválida:

```python
STANDARD_USER = {
    "username": "standard_user",
    "password": "wrong_password",   # ← cambio temporal
}
```

2. Ejecutar los tests:

```bash
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css
```

3. Abrir el reporte y verificar:
   - La tarjeta **Failed/Error** muestra 1 (o más).
   - La fila de `test_valid_login` está en rojo.
   - En la columna **Links** de esa fila hay un link/imagen. Expandirlo para ver el screenshot.

4. **Restaurar** el valor original antes de continuar:

```python
STANDARD_USER = {
    "username": "standard_user",
    "password": "secret_sauce",     # ← restaurar
}
```

### Qué esperar ver en el screenshot

Una captura de la pantalla de login de SauceDemo con el mensaje de error "Epic sadface: Username and password do not match any user in this service".

---

## Ejercicio 3: Generar el reporte Allure y navegar por suites y pasos

### Objetivo

Generar los datos de Allure y explorar la interfaz interactiva: suites, pasos, gráfico de dona.

### Prerequisito

Allure CLI instalado:

```bash
allure --version
```

### Pasos

1. Ejecutar los tests generando datos de Allure:

```bash
pytest tests/ --alluredir=allure-results
```

2. Abrir el reporte en el navegador:

```bash
allure serve allure-results
```

Se abre automáticamente en el browser en una URL del tipo `http://localhost:XXXX`.

3. Explorar:
   - **Overview**: gráfico de dona, estadísticas.
   - **Suites**: expandir hasta llegar a un test individual, ver los pasos.
   - **Behaviors**: ver la jerarquía Epic → Feature → Story.
   - Clic en un test individual: ver los pasos con sus tiempos.

### Preguntas para responder

- ¿Cuántos pasos tiene `test_valid_login` en el reporte?
- ¿Qué story aparece para `test_login_error_messages_for_invalid_scenarios`?
- ¿Cuál es la severidad de `test_valid_login`?

---

## Ejercicio 4: Ejecutar ambos reportes al mismo tiempo

### Objetivo

Ejecutar pytest generando el reporte HTML y los datos de Allure simultáneamente (como lo hace CI).

### Pasos

1. Ejecutar:

```bash
pytest tests/ \
  --html=reports/report.html \
  --self-contained-html \
  --css=reports/academy_report.css \
  --alluredir=allure-results \
  -v
```

En Windows (PowerShell, sin multiline):

```powershell
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css --alluredir=allure-results -v
```

2. Abrir el reporte HTML:

```powershell
start reports/report.html
```

3. Abrir el reporte Allure (en otra terminal):

```bash
allure serve allure-results
```

4. Comparar la misma ejecución vista desde los dos reportes:
   - ¿Qué información tiene uno que el otro no?
   - ¿Cuál es más útil para una revisión rápida?
   - ¿Cuál es más útil para debug?

---

## Ejercicio 5: Headless vs headed

### Objetivo

Comprender la diferencia entre ejecución headless (sin browser visible) y headed (con browser visible).

### Modo headless (por defecto)

```bash
pytest tests/ -v
```

No abre el browser. Más rápido, sin distracciones, ideal para CI.

### Modo headed

```bash
pytest tests/ --headed -v
```

Abre el browser de Chromium visible y podés ver cada interacción en tiempo real.

### Pasos

1. Ejecutar en modo headed:

```bash
pytest tests/ --headed -v
```

2. Observar el browser abrirse y ejecutar los tests.
3. Notar que es más lento que headless.

### Modo debug (Playwright Inspector)

Para ejecutar un solo test con el Inspector de Playwright (paso a paso):

```powershell
# Windows PowerShell
$env:PWDEBUG=1; pytest tests/test_login.py::test_valid_login -s
```

Se abre el **Playwright Inspector**: podés ejecutar paso a paso, ver el DOM y usar "Pick locator".

---

## Ejercicio 6: Modo solo para un test

### Objetivo

Practicar cómo ejecutar un test específico en lugar de toda la suite.

### Por nombre de función

```bash
pytest tests/test_login.py::test_valid_login -v
```

### Por id de parámetro (parametrized)

```bash
pytest tests/ -k "locked_user_cannot_log_in" -v
```

### Solo tests fallidos de la última ejecución

```bash
pytest tests/ --lf -v
```

(`--lf` = last failed)

### Reejecutar fallidos hasta 3 veces (retry)

```bash
pytest tests/ --reruns 3 -v
```

---

## Resumen de comandos

| Objetivo | Comando |
|----------|---------|
| Solo HTML | `pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css` |
| Solo Allure | `pytest tests/ --alluredir=allure-results` |
| Ambos reportes | `pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css --alluredir=allure-results` |
| Ver Allure en browser | `allure serve allure-results` |
| Allure estático | `allure generate allure-results --clean -o allure-report && allure open allure-report` |
| Con browser visible | `pytest tests/ --headed` |
| Un test específico | `pytest tests/test_login.py::test_valid_login -v` |
| Por keyword | `pytest tests/ -k "locked_user"` |
| Solo fallidos | `pytest tests/ --lf` |
| Debug paso a paso | `$env:PWDEBUG=1; pytest tests/test_login.py -s` |
