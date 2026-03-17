# Documentación — Academy E2E Automation

Documentación técnica completa del proyecto de automatización E2E con pytest, Playwright y Page Object Model.

---

## Índice de documentos

| # | Documento | Qué cubre |
|---|-----------|-----------|
| 01 | [Estructura del proyecto](01-PROJECT_STRUCTURE.md) | Árbol de archivos, stack, flujo de ejecución |
| 02 | [Page Object Model](02-PAGE_OBJECT_MODEL.md) | Patrón POM, LoginPage, datos, configuración |
| 03 | [conftest.py y hooks](03-CONFTEST_AND_HOOKS.md) | Hooks de pytest, dashboard, screenshots |
| 04 | [Allure Report](04-ALLURE_REPORT.md) | Integración, decoradores, ejecución local y CI |
| 05 | [CI/CD](05-CI_CD.md) | GitHub Actions, artifacts, GitHub Pages |

---

## Ejercicios prácticos

Los ejercicios están en la carpeta [`exercises/`](exercises/README.md):

| # | Ejercicio | Tema |
|---|-----------|------|
| 01 | [Personalizar el reporte CSS](exercises/01-CUSTOMIZE_REPORT_CSS.md) | Modificar `academy_report.css` |
| 02 | [Correr los reportes](exercises/02-RUNNING_REPORTS.md) | pytest-html vs Allure en práctica |
| 03 | [Extender Page Objects](exercises/03-EXTEND_PAGE_OBJECTS.md) | Crear un nuevo Page Object |

---

## Estructura de carpetas

```
docs/
  README.md                    <- este archivo
  01-PROJECT_STRUCTURE.md
  02-PAGE_OBJECT_MODEL.md
  03-CONFTEST_AND_HOOKS.md
  04-ALLURE_REPORT.md
  05-CI_CD.md
  exercises/
    README.md
    01-CUSTOMIZE_REPORT_CSS.md
    02-RUNNING_REPORTS.md
    03-EXTEND_PAGE_OBJECTS.md
```

---

## Referencia rápida de comandos

```bash
# Ejecutar todos los tests (headless)
pytest tests/

# Reporte HTML (tema Academy)
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css

# Reporte Allure (datos)
pytest tests/ --alluredir=allure-results

# Ver reporte Allure en el navegador
allure serve allure-results

# Debug con browser visible
pytest tests/ --headed

# Debug paso a paso con Inspector
$env:PWDEBUG=1; pytest tests/test_login.py -s
```
