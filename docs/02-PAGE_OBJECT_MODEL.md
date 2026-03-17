# 02 — Page Object Model (POM)

Este documento explica el patrón Page Object Model, por qué se utiliza en este proyecto y cómo está implementado en `pages/login_page.py`.

---

## Tabla de contenidos

1. [¿Qué problema resuelve POM?](#qué-problema-resuelve-pom)
2. [¿Qué es el Page Object Model?](#qué-es-el-page-object-model)
3. [Diagrama de capas](#diagrama-de-capas)
4. [Implementación en este proyecto](#implementación-en-este-proyecto)
5. [Análisis de LoginPage](#análisis-de-loginpage)
6. [Separación de datos: `data/users.py`](#separación-de-datos-datauserspy)
7. [Configuración centralizada: `utils/config.py`](#configuración-centralizada-utilsconfigpy)
8. [Integración con Allure: `@allure.step`](#integración-con-allure-allurestep)
9. [Comparación: con POM vs sin POM](#comparación-con-pom-vs-sin-pom)
10. [Reglas del patrón aplicadas aquí](#reglas-del-patrón-aplicadas-aquí)

---

## ¿Qué problema resuelve POM?

Cuando los tests interactúan directamente con el browser usando locators, ocurre lo siguiente:

```python
# Sin POM: el locator está en el test
def test_login(page):
    page.locator("//input[@id='user-name']").fill("standard_user")
    page.locator("//input[@id='password']").fill("secret_sauce")
    page.locator("//input[@id='login-button']").click()
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
```

Si el id `user-name` cambia en el HTML del sitio, hay que buscar y editar **todos** los tests que lo usen.

Con 5 tests distintos que hacen login, tenés 5 lugares donde corregir. Esto viola el principio **DRY** (Don't Repeat Yourself) y hace el mantenimiento costoso.

**POM resuelve esto** encapsulando los locators y acciones en un objeto, de modo que los tests quedan limpios y el único lugar a actualizar ante un cambio de UI es el Page Object.

---

## ¿Qué es el Page Object Model?

POM es un **patrón de diseño** para automatización de UI. La idea central es:

> Cada pantalla o componente importante de la aplicación tiene su propia clase Python que encapsula los locators y las acciones que se pueden hacer en esa pantalla.

Los tests **no interactúan directamente con el browser**: llaman métodos del Page Object, que a su vez maneja los locators.

```
Tests → Page Objects → Browser (Playwright)
```

Beneficios:

| Beneficio | Descripción |
|-----------|-------------|
| **Mantenibilidad** | Si la UI cambia, solo se actualiza el Page Object |
| **Legibilidad** | Los tests leen como especificaciones, no como código de UI |
| **Reutilización** | El mismo Page Object se usa en múltiples tests |
| **Separación de responsabilidades** | El test define QUÉ validar; el PO define CÓMO interactuar |

---

## Diagrama de capas

```
test_login.py
  test_valid_login(page)
    login_page = LoginPage(page)    <- instancia el PO
    login_page.goto()               <- acción
    login_page.login_as(user)       <- acción
    login_page.assert_inventory_loaded()  <- aserción
         |
         | llama métodos
         v
    LoginPage
      __init__(page)
        self.username_input = page.locator(...)  <- locator
        self.password_input = page.locator(...)
        self.login_button   = page.locator(...)
        self.error_message  = page.locator(...)

      goto()       -> page.goto(BASE_URL)
      login(u, p)  -> fill + click
      login_as(u)  -> login(user["username"], ...)
      assert_inventory_loaded() -> expect(page).to_have_url(...)
         |
         | llama API Playwright
         v
    Playwright (browser) — Chromium / Firefox / WebKit
```

---

## Implementación en este proyecto

```
pages/
  login_page.py    <- Page Object de la pantalla de login de SauceDemo
```

La pantalla bajo prueba es `https://www.saucedemo.com/` — la pantalla de login de SauceDemo.

Un Page Object por pantalla es la convención. Si se agregara soporte para la pantalla de inventario, se crearía `pages/inventory_page.py`.

---

## Análisis de LoginPage

### Constructor: definición de locators

```python
class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username_input = page.locator("//input[@id='user-name']")
        self.password_input = page.locator("//input[@id='password']")
        self.login_button   = page.locator("//input[@id='login-button']")
        self.error_message  = page.locator("//h3[@data-test='error']")
```

**Por qué los locators se definen en `__init__`:**

1. **Un único lugar para cambiarlos.** Si el HTML cambia, se actualiza el locator aquí y todos los métodos que lo usan se benefician automáticamente.
2. **Playwright es lazy.** `page.locator(...)` no busca el elemento en el DOM de inmediato; solo crea un objeto que lo buscará cuando se interactúe con él. Por eso es seguro crearlos en el constructor antes de que la página cargue.
3. **Legibilidad.** Los nombres (`username_input`, `login_button`) son semánticos y más fáciles de leer en los métodos que la cadena XPath completa.

**Tipos de locators usados:**

| Locator | Selector | Por qué |
|---------|----------|---------|
| `username_input` | `//input[@id='user-name']` | XPath por atributo `id` — estable si el id no cambia |
| `password_input` | `//input[@id='password']` | Igual |
| `login_button` | `//input[@id='login-button']` | Igual |
| `error_message` | `//h3[@data-test='error']` | `data-test` es el atributo más recomendado: no cambia con refactors de CSS o layout |

> **Preferir `data-test` sobre `id`/clase CSS.** Los atributos `data-test` son puestos por el equipo de desarrollo explícitamente para testing y no se modifican durante refactors visuales.

---

### Acción: `goto()`

```python
@allure.step("Navegar a la página de login")
def goto(self):
    self.page.goto(BASE_URL)
    self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)
```

- Navega a la URL base definida en `utils/config.py`.
- Aplica el timeout global para todas las interacciones siguientes en esta página.
- El `@allure.step` hace que en el reporte Allure aparezca como un paso nombrado dentro del test.

---

### Acción: `login(username, password)`

```python
@allure.step("Ingresar credenciales: usuario={username}, contraseña={password}")
def login(self, username: str, password: str):
    self.username_input.fill(username)
    self.password_input.fill(password)
    self.login_button.click()
```

- Acepta credenciales crudas (strings).
- `fill()` limpia el campo antes de escribir (más robusto que `type()`).
- El decorador `@allure.step` muestra el username en el nombre del paso gracias al template `{username}`.

---

### Acción: `login_as(user)`

```python
@allure.step("Iniciar sesión como usuario")
def login_as(self, user: dict) -> None:
    self.login(user["username"], user["password"])
```

Variante de `login` que acepta un diccionario `{username, password}`. Permite escribir tests más expresivos:

```python
login_page.login_as(STANDARD_USER)   # vs
login_page.login("standard_user", "secret_sauce")
```

La primera versión comunica la **intención** (iniciar sesión como usuario estándar), no los detalles de implementación.

---

### Aserción: `assert_inventory_loaded()`

```python
@allure.step("Verificar redirección al inventario tras login exitoso")
def assert_inventory_loaded(self) -> None:
    expect(self.page).to_have_url(f"{BASE_URL}inventory.html")
    expect(self.page).to_have_title("Swag Labs")
```

**Por qué las aserciones están en el Page Object y no en el test:**

1. **Reutilización.** Si 5 tests validan que se llegó al inventario, la lógica de aserción está en un solo lugar.
2. **Encapsulamiento.** El test dice "verificar que llegamos al inventario"; el Page Object sabe QUÉ verificar exactamente (URL + título).
3. **Mantenibilidad.** Si cambia la URL del inventario, se actualiza solo aquí.
4. **Legibilidad del test.** El test queda como una lista de pasos de alto nivel.

`expect()` es el helper de aserciones de Playwright. A diferencia de un `assert` simple, tiene auto-retry con timeout, lo que lo hace más robusto para UIs asíncronas.

---

### Aserción: `assert_error_contains(message)`

```python
@allure.step("Verificar que el mensaje de error contiene: '{message}'")
def assert_error_contains(self, message: str) -> None:
    expect(self.error_message).to_contain_text(message)
```

- Usa `to_contain_text` (no `to_have_text`) para validar que el mensaje está contenido, siendo más resiliente a cambios menores en el texto.
- El template `'{message}'` en el step muestra el mensaje esperado en el reporte Allure.

---

## Separación de datos: `data/users.py`

```python
STANDARD_USER = {"username": "standard_user", "password": "secret_sauce"}
LOCKED_USER   = {"username": "locked_out_user", "password": "secret_sauce"}
INVALID_USER  = {"username": "invalid_user", "password": "wrong_password"}
```

**Por qué los datos están separados del test:**

- Los tests no tienen credenciales hardcodeadas, son fáciles de leer.
- Si las credenciales cambian, se actualiza solo `users.py`.
- Se pueden agregar nuevos usuarios sin tocar el test.
- Posibilita leer datos desde variables de entorno o archivos externos en el futuro.

Los diccionarios `{username, password}` coinciden con la interfaz que espera `login_as()`, lo que hace el código muy fluido:

```python
login_page.login_as(STANDARD_USER)
login_page.login_as(LOCKED_USER)
login_page.login_as(INVALID_USER)
```

---

## Configuración centralizada: `utils/config.py`

```python
BASE_URL = "https://www.saucedemo.com/"
DEFAULT_TIMEOUT_MS = 10000
```

**Por qué centralizar la URL:**

- Si el entorno cambia (staging, producción), se modifica un solo archivo.
- Es importada en `LoginPage.goto()` y en `conftest.py` (para el reporte).
- Evita que la URL esté hardcodeada en múltiples lugares.

**Por qué centralizar el timeout:**

- 10 segundos es el tiempo razonable para esperar elementos en una conexión estándar.
- Al estar en `config.py`, se puede ajustar globalmente sin buscar en todos los Page Objects.

---

## Integración con Allure: `@allure.step`

Cada método público de `LoginPage` tiene el decorador `@allure.step(...)`:

```python
@allure.step("Navegar a la página de login")
def goto(self): ...

@allure.step("Ingresar credenciales: usuario={username}, contraseña={password}")
def login(self, username: str, password: str): ...
```

**Qué hace `@allure.step`:**

- Cuando se ejecuta el test, Allure registra la entrada y salida de cada método decorado.
- En el reporte, el test muestra una **jerarquía de pasos** con sus tiempos:

```
test_valid_login
  |-- [PASO] Navegar a la página de login          (0.8s)
  |-- [PASO] Iniciar sesión como usuario            (0.4s)
  |     |-- [PASO] Ingresar credenciales: usuario=standard_user   (0.3s)
  |-- [PASO] Verificar redirección al inventario    (0.2s)
```

Los templates con `{param}` en el nombre del step toman el valor real del argumento. Esto hace los reportes mucho más informativos.

---

## Comparación: con POM vs sin POM

### Sin POM

```python
def test_valid_login(page):
    page.goto("https://www.saucedemo.com/")
    page.set_default_timeout(10000)
    page.locator("//input[@id='user-name']").fill("standard_user")
    page.locator("//input[@id='password']").fill("secret_sauce")
    page.locator("//input[@id='login-button']").click()
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")

def test_locked_user(page):
    page.goto("https://www.saucedemo.com/")            # duplicado
    page.set_default_timeout(10000)                    # duplicado
    page.locator("//input[@id='user-name']").fill("locked_out_user")  # duplicado
    page.locator("//input[@id='password']").fill("secret_sauce")      # duplicado
    page.locator("//input[@id='login-button']").click()               # duplicado
    expect(page.locator("//h3[@data-test='error']")).to_contain_text("locked out")
```

### Con POM

```python
def test_valid_login(page):
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login_as(STANDARD_USER)
    login_page.assert_inventory_loaded()

def test_locked_user(page):
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login_as(LOCKED_USER)
    login_page.assert_error_contains("locked out")
```

Los tests con POM son más cortos, expresivos y sin duplicación.

---

## Reglas del patrón aplicadas aquí

| Regla | Cómo se aplica |
|-------|---------------|
| Un PO por pantalla | `LoginPage` para login; si hubiera inventario: `InventoryPage` |
| Locators solo en el PO | Ningún `page.locator()` en los tests |
| Lógica de interacción en el PO | Los tests solo llaman métodos semánticos |
| Aserciones en el PO | `assert_*` encapsulan el `expect()` |
| Datos separados | `data/users.py` fuera del PO y del test |
| Config centralizada | `utils/config.py` importada en el PO |
| Steps en el PO | `@allure.step` decora métodos del PO, no código del test |
