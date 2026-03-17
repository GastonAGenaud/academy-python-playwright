# Ejercicio 01 — Personalizar el reporte CSS

En este ejercicio vas a modificar `reports/academy_report.css` para cambiar la apariencia visual del reporte HTML generado por pytest-html. Vas a aprender cómo está estructurado el CSS, qué controla cada sección y cómo verificar los cambios.

---

## Antes de empezar

### Dónde está el CSS

```
reports/
  academy_report.css   <- este archivo
  report.html          <- el reporte generado (se recrea en cada ejecución)
```

### Cómo regenerar el reporte para ver cambios

```bash
pytest tests/ --html=reports/report.html --self-contained-html --css=reports/academy_report.css
```

Luego abrir `reports/report.html` en el navegador. En Windows:

```powershell
start reports/report.html
```

### Estructura del CSS (resumen)

```css
:root { /* variables de color y tipografía */ }
body  { /* fondo, fuente base */ }
h1    { /* título principal */ }
.academy-dashboard { /* grid de tarjetas */ }
.academy-card      { /* tarjeta individual */ }
.academy-banner    { /* franja informativa */ }
#environment       { /* tabla de metadatos */ }
table, thead, tbody { /* tabla de resultados */ }
span.passed / .failed / .skipped { /* colores de estado */ }
```

---

## Ejercicio 1: Cambiar la paleta de colores

### Objetivo

Cambiar el tema del reporte de oscuro a un tema claro con identidad propia.

### Qué modificar

Abrí `reports/academy_report.css` y encontrá el bloque `:root`:

```css
:root {
  --bg: #0f1419;
  --surface: #1a2332;
  --surface2: #243044;
  --text: #e8edf4;
  --muted: #8b9cb3;
  --accent: #c9a227;
  --pass: #3d9a6e;
  --fail: #e85d5d;
  --skip: #d4a03c;
  --border: rgba(201, 162, 39, 0.22);
  --radius: 10px;
}
```

### Tu tarea

Reemplazá las variables para crear un **tema claro** con la siguiente paleta:

| Variable | Valor propuesto | Descripción |
|----------|-----------------|-------------|
| `--bg` | `#f5f7fa` | Fondo principal gris muy claro |
| `--surface` | `#ffffff` | Fondo de cards y tablas |
| `--surface2` | `#eef1f6` | Fondo de encabezados de tabla |
| `--text` | `#1a202c` | Texto principal oscuro |
| `--muted` | `#718096` | Texto secundario |
| `--accent` | `#2b6cb0` | Azul corporativo |
| `--pass` | `#276749` | Verde oscuro |
| `--fail` | `#c53030` | Rojo |
| `--skip` | `#b7791f` | Naranja |
| `--border` | `rgba(43, 108, 176, 0.2)` | Borde azul sutil |

### Pasos

1. Editá el bloque `:root` con los valores de la tabla.
2. Regenerá el reporte.
3. Abrilo en el navegador y verificá que el fondo sea claro.

### Resultado esperado

El reporte debe verse con fondo blanco/gris claro, texto oscuro y acentos azules.

---

## Ejercicio 2: Cambiar las tipografías

### Objetivo

Reemplazar las fuentes de Google Fonts por otras de tu elección.

### Qué modificar

Al inicio del CSS hay una importación de Google Fonts:

```css
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:...");
```

Y más abajo se usan:

```css
body {
  font-family: "DM Sans", system-ui, sans-serif;
}

h1 {
  font-family: "Instrument Serif", Georgia, serif;
}
```

### Tu tarea

Elegí dos fuentes de [Google Fonts](https://fonts.google.com/) — una sans-serif para el cuerpo y una con personalidad para el título — y actualizá:

1. El `@import` con las nuevas fuentes.
2. `font-family` en `body` y `h1`.

### Sugerencias de pares tipográficos

| Título (h1) | Cuerpo (body) |
|-------------|---------------|
| Playfair Display | Source Sans 3 |
| Fraunces | Nunito Sans |
| Syne | Inter |
| Bebas Neue | Lato |

### Pasos

1. Ir a https://fonts.google.com/, buscar las fuentes deseadas.
2. Clic en **Get font** → **Get embed code** → copiar el `@import`.
3. Reemplazar el `@import` al inicio del CSS.
4. Actualizar los `font-family` en `body` y `h1`.
5. Regenerar el reporte y verificar.

---

## Ejercicio 3: Agregar una nueva tarjeta al dashboard

### Objetivo

Agregar una 6ta tarjeta al dashboard que muestre la **URL bajo prueba** (`BASE_URL`).

Este ejercicio involucra dos archivos: el CSS y `conftest.py`.

### Parte A: el CSS

Agregar al final de `academy_report.css`:

```css
.academy-card--url .academy-card__value {
  font-size: 0.8rem;
  word-break: break-all;
  color: var(--accent);
}
```

### Parte B: conftest.py

En `conftest.py`, dentro de `pytest_html_results_summary`, el dashboard se construye como string HTML. Encontrá la tarjeta de Duration y, **después** de ella, agregar:

```python
      <div class="academy-card academy-card--url">
        <div class="academy-card__value">{html.escape(BASE_URL)}</div>
        <div class="academy-card__label">Base URL</div>
      </div>
```

### Pasos

1. Agregar el CSS de `.academy-card--url` al final del archivo CSS.
2. Agregar la tarjeta en el f-string de `conftest.py`.
3. Regenerar el reporte.
4. Verificar que aparece la 6ta tarjeta con la URL.

---

## Ejercicio 4: Agregar animaciones a las tarjetas

### Objetivo

Hacer que las tarjetas del dashboard aparezcan con una animación de entrada al cargar el reporte.

### Qué agregar al CSS

Al final de `academy_report.css`, agregar:

```css
@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.academy-card {
  animation: card-in 0.4s ease both;
}

.academy-dashboard .academy-card:nth-child(1) { animation-delay: 0.0s; }
.academy-dashboard .academy-card:nth-child(2) { animation-delay: 0.1s; }
.academy-dashboard .academy-card:nth-child(3) { animation-delay: 0.2s; }
.academy-dashboard .academy-card:nth-child(4) { animation-delay: 0.3s; }
.academy-dashboard .academy-card:nth-child(5) { animation-delay: 0.4s; }
```

### Pasos

1. Agregar el bloque CSS al final del archivo.
2. Regenerar el reporte.
3. Abrirlo en el navegador y recargar la página para ver la animación.

### Para ir más lejos: efecto hover

```css
.academy-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.academy-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}
```

---

## Soluciones

### Ejercicio 1

Reemplazar el bloque `:root` con los valores de la tabla. El CSS usa las variables automáticamente; no hay más cambios.

### Ejercicio 2

Ejemplo con Fraunces + Nunito Sans:

```css
@import url("https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;1,400&family=Nunito+Sans:wght@400;600&display=swap");

body  { font-family: "Nunito Sans", system-ui, sans-serif; }
h1    { font-family: "Fraunces", Georgia, serif; }
```

### Ejercicio 3

CSS al final del archivo:
```css
.academy-card--url .academy-card__value {
  font-size: 0.8rem;
  word-break: break-all;
  color: var(--accent);
}
```

En `conftest.py`, dentro del f-string `dash`, después de la tarjeta Duration:
```python
      <div class="academy-card academy-card--url">
        <div class="academy-card__value">{html.escape(BASE_URL)}</div>
        <div class="academy-card__label">Base URL</div>
      </div>
```

### Ejercicio 4

El CSS del ejercicio es la solución completa. Solo copiarlo al final del archivo.
