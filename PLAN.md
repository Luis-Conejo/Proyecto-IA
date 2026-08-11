# PLAN.md — Plan de implementación de la app de certificados

## Objetivo

Automatizar la emisión de certificados de **Academia Horizonte** como aplicación web, leyendo los Excel de `Insumos/` (solo lectura) y aplicando las reglas de negocio del `AGENTS.md`.

## Decisiones técnicas (acordadas en modo Plan)

- **Lectura de Excel:** `pandas` (por encima de `openpyxl`) para leer y agrupar los datos.
- **Servidor web:** `Flask` (se instala con `pip install flask`).
- **Lógica de negocio:** 100 % en `app.py` (la "Cocina"), nunca en la interfaz (el "Salón" solo muestra).
- **Estructura prevista:**

  ```
  ProyectoCertificadosUniversidad/
  ├── app.py              # Flask: lectura, cálculo y reglas de negocio
  ├── templates/          # HTML servidos por Flask (index, certificado)
  ├── static/style.css    # Diseño azul marino y dorado
  └── Insumos/            # Bodega: solo lectura, NUNCA se modifica
  ```

- Scripts auxiliares de una sola tarea usan prefijo `_` (convención heredada).

## Casos borde y decisiones acordadas

1. **`304560321` (Espinoza Leon Javier):** está en el maestro pero no tiene notas → se muestra como "sin datos de evaluación", no genera certificado.
2. **`999880777`:** tiene 4 notas pero no existe en el maestro → se genera su certificado con los datos disponibles, pero marcado como incidencia "sin registro en maestro" (no hay nombre ni correo).
3. **Módulos por programa:** `Técnico en IA Aplicada` = 4 módulos; `Excel Avanzado para Negocios` = 3 módulos. El promedio divide entre los módulos cursados.

## Fases

### Fase 0 — Documentación (esta)

- Crear `PLAN.md` y corregir/actualizar `AGENTS.md` (24 estudiantes, 2 programas, cabecera `Identificacion`, decisiones técnicas).
- **Validación:** revisión del usuario en modo Plan.

### Fase 1 — Validación del cruce de datos

- Crear `_validar_datos.py`: lee ambos Excel (sin modificarlos) y reporta:
  - cabeceras y número de filas de cada archivo;
  - estudiantes por programa y módulos por programa;
  - IDs del maestro sin notas (`304560321`);
  - IDs en evaluaciones sin maestro (`999880777`);
  - duplicados de `(Identificación, Programa, Módulo)`;
  - valores fuera de rango 0–100, no numéricos o campos vacíos;
  - estado esperado de certificados (conteo por tipo).
- **Validación:** ejecutar `python _validar_datos.py` y comparar la salida con los valores esperados del análisis: 24 grupos, **20 Aprobación / 3 Participación / 1 Sin certificado**, 2 incidencias detectadas.

### Fase 2 — Backend Flask (la Cocina)

- Instalar `flask`.
- Crear `app.py` con:
  - `leer_datos()`: carga ambos Excel a DataFrames;
  - `calcular_resultados()`: agrupa por `Identificación + Programa`, calcula promedio y asistencia, clasifica (aprobación / participación / sin certificado) y detecta incidencias;
  - rutas `/` y `/certificado/<identificacion>`, devolviendo primero **JSON** para validar la lógica sin interfaz.
- **Validación:** ejecutar `python app.py`, consultar las rutas (navegador o `curl`) y comprobar: 24 certificados (20/3/1), incidencias visibles en la respuesta y promedio correcto de un caso conocido.

### Fase 3 — Interfaz web (el Salón)

- `templates/index.html`: tabla resumen de certificados (estudiante, programa, promedio, asistencia, estado).
- `templates/certificado.html`: ficha de un estudiante (datos, promedios, estado).
- `static/style.css`: azul marino y dorado.
- Mostrar las incidencias (`999880777` sin nombre; `304560321` sin datos).
- **Validación:** navegar la app y revisar: los 3 estados visibles, los 2 casos borde, y el diseño.

### Fase 4 — Prueba integral

- Comprobar: totales (24 / 20 / 3 / 1) vs. el análisis, navegación entre páginas y manejo de IDs inexistentes en la URL (404).
- **Validación:** recorrido manual completo + repaso del código con el usuario.

## Criterios de aceptación

- Los totales de la app coinciden con el análisis: 24 certificados → 20 Aprobación, 3 Participación, 1 Sin certificado.
- Las incidencias de datos son visibles en la interfaz.
- El frontend no contiene cálculos ni reglas de negocio (solo muestra).
- Código simple y comentado en español, señalando variables, tipos, condicionales, bucles y funciones.
