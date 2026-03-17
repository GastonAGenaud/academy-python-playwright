# Ejercicio 03 — Extender Page Objects

En este ejercicio vas a crear un nuevo Page Object para la pantalla de inventario de SauceDemo (la que aparece después de un login exitoso). Vas a practicar el patrón POM desde cero, incluyendo locators, acciones, aserciones y decoradores de Allure.

---

## Contexto

Cuando `test_valid_login` hace login exitoso, el browser navega a:

```
https://www.saucedemo.com/inventory.html
```

Esta pantalla muestra una grilla de productos. Actualmente `assert_inventory_loaded()` solo verifica la URL y el título, pero no valida nada del contenido de la pantalla.

El ejercicio es crear `pages/inventory_page.py` con un Page Object que encapsule interacciones con esa pantalla.

---

## Parte 1: Explorar la pantalla

### Paso 1: Ejecutar el test en modo headed para ver la pantalla

```bash
pytest tests/test_login.py::test_valid_login --headed -v
```

Observar qué elementos hay en la pantalla de inventario.

### Paso 2: Inspeccionar el HTML (DevTools)

Abrir el navegador en `https://www.saucedemo.com/`, iniciar sesión manualmente con:

- Username: `standard_user`
- Password: `secret_sauce`

Luego abrir DevTools (F12) e inspeccionar los elementos clave:

| Elemento | Selector sugerido |
|----------|------------------|
| Título "Products" | `//span[@class='title']` |
| Lista de items | `//div[@class='inventory_list']` |
| Nombre de primer producto | `(//div[@class='inventory_item_name'])[1]` |
| Botón "Add to cart" del primer item | `(//button[contains(@class,'btn_inventory')])[1]` |
| Ícono del carrito | `//a[@class='shopping_cart_link']` |
| Badge del carrito (cantidad) | `//span[@class='shopping_cart_badge']` |
| Menú hamburguesa | `//button[@id='react-burger-menu-btn']` |

---

## Parte 2: Crear el Page Object

### Estructura del archivo

Crear `pages/inventory_page.py` con la siguiente estructura:

```python
import allure
from playwright.sync_api import Page, expect


class InventoryPage:
    """Page Object for SauceDemo inventory screen (post-login)."""

    def __init__(self, page: Page):
        self.page = page
        # Definir locators aquí

    # Definir métodos aquí
```

### Tu tarea

Implementar los locators y métodos indicados abajo. Intentarlo por tu cuenta antes de ver la solución.

#### Locators a definir en `__init__`

| Nombre del locator | Qué elemento representa |
|--------------------|------------------------|
| `self.page_title` | El `<span>` con el texto "Products" |
| `self.product_list` | El contenedor de todos los productos |
| `self.cart_link` | El ícono del carrito (link) |
| `self.cart_badge` | El badge numérico del carrito |

#### Métodos a implementar

| Método | Qué hace |
|--------|---------|
| `get_product_names()` | Retorna una lista de strings con los nombres de todos los productos visibles |
| `add_first_item_to_cart()` | Hace clic en el botón "Add to cart" del primer producto |
| `get_cart_count()` | Retorna el número en el badge del carrito (int). Si el badge no está visible, retorna 0 |
| `assert_page_loaded()` | Verifica que la página tiene el título "Products" y la URL contiene `inventory.html` |
| `assert_cart_has_items(count)` | Verifica que el badge del carrito muestra el número esperado |

#### Requisito adicional

Todos los métodos deben estar decorados con `@allure.step(...)`.

---

## Parte 3: Crear un test que use InventoryPage

### Crear `tests/test_inventory.py`

```python
"""Inventory page E2E tests."""

import allure
import pytest

from data.users import STANDARD_USER
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage


@allure.epic("SauceDemo E2E")
@allure.feature("Inventory")
@allure.story("Visualización del inventario")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("El inventario muestra productos después del login")
def test_inventory_shows_products(page):
    """Validate that the inventory page loads and shows products."""
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login_as(STANDARD_USER)

    inventory_page = InventoryPage(page)
    inventory_page.assert_page_loaded()

    # Verificar que hay al menos un producto
    product_names = inventory_page.get_product_names()
    assert len(product_names) > 0


@allure.epic("SauceDemo E2E")
@allure.feature("Inventory")
@allure.story("Agregar al carrito")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Agregar el primer producto al carrito actualiza el badge")
def test_add_item_to_cart(page):
    """Validate that adding an item updates the cart badge."""
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login_as(STANDARD_USER)

    inventory_page = InventoryPage(page)
    inventory_page.add_first_item_to_cart()
    inventory_page.assert_cart_has_items(1)
```

### Ejecutar los nuevos tests

```bash
pytest tests/test_inventory.py -v --headed
```

---

## Parte 4: Verificar en los reportes

### Reporte HTML

```bash
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css
start reports/report.html
```

Verificar que los nuevos tests aparecen en la tabla.

### Reporte Allure

```bash
pytest tests/ --alluredir=allure-results
allure serve allure-results
```

En la sección **Behaviors**, verificar que aparece el Feature "Inventory" bajo el Epic "SauceDemo E2E".

---

## Solución completa: `pages/inventory_page.py`

```python
import allure
from playwright.sync_api import Page, expect

from utils.config import BASE_URL


class InventoryPage:
    """Page Object for SauceDemo inventory screen (post-login)."""

    def __init__(self, page: Page):
        """Create page locators once to reuse them across tests."""
        self.page = page
        self.page_title = page.locator("//span[@class='title']")
        self.product_list = page.locator("//div[@class='inventory_list']")
        self.cart_link = page.locator("//a[@class='shopping_cart_link']")
        self.cart_badge = page.locator("//span[@class='shopping_cart_badge']")

    @allure.step("Obtener nombres de productos visibles")
    def get_product_names(self) -> list[str]:
        """Return a list of all visible product names."""
        items = self.page.locator("//div[@class='inventory_item_name']")
        return [items.nth(i).inner_text() for i in range(items.count())]

    @allure.step("Agregar el primer producto al carrito")
    def add_first_item_to_cart(self) -> None:
        """Click 'Add to cart' button of the first product."""
        first_button = self.page.locator("//button[contains(@class,'btn_inventory')]").first
        first_button.click()

    @allure.step("Obtener cantidad en el carrito")
    def get_cart_count(self) -> int:
        """Return the cart badge count. Returns 0 if badge is not visible."""
        if self.cart_badge.is_visible():
            return int(self.cart_badge.inner_text())
        return 0

    @allure.step("Verificar que la página de inventario está cargada")
    def assert_page_loaded(self) -> None:
        """Assert the inventory page title and URL are correct."""
        expect(self.page).to_have_url(f"{BASE_URL}inventory.html")
        expect(self.page_title).to_have_text("Products")

    @allure.step("Verificar que el carrito tiene {count} item(s)")
    def assert_cart_has_items(self, count: int) -> None:
        """Assert the cart badge shows the expected count."""
        expect(self.cart_badge).to_have_text(str(count))
```

---

## Checklist de verificación

Al completar el ejercicio, los siguientes puntos deben cumplirse:

- [ ] `pages/inventory_page.py` existe y tiene los 5 métodos.
- [ ] Todos los métodos tienen `@allure.step`.
- [ ] `tests/test_inventory.py` tiene 2 tests con decoradores de Allure.
- [ ] `pytest tests/ -v` corre sin errores (incluye los nuevos tests).
- [ ] En el reporte HTML, los tests de inventory aparecen en la tabla.
- [ ] En Allure, el Feature "Inventory" aparece bajo el Epic "SauceDemo E2E".
- [ ] En Allure, cada test muestra los pasos de `LoginPage` + `InventoryPage`.
