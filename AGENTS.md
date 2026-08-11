# AGENTS.md — ProyectoCertificadosUniversidad

Instrucciones para agentes de OpenCode trabajando en este proyecto. Los archivos `AGENTS.md` y `CLAUDE.md` en `Universidad Fundepos\` (raíz del workspace) también aplican: mapa de módulos, convención de español y contexto general del programa.

- **Idioma (obligatorio):** Todas las respuestas y entregables deben escribirse en **español** (mensajes, comentarios de código, notebooks, documentación).

## Contexto del proyecto

**Academia Horizonte**, centro de formación que imparte programas técnicos a empresas. Al cerrar cada cohorte emite certificados por estudiante. Hoy el proceso es manual en Excel y Word; lo estamos automatizando como una **aplicación web**.

## Arquitectura (3 piezas)

- **Bodega (datos):** los Excel en `Insumos/`. **NO se modifican** (son la fuente oficial de lectura).
- **Cocina (backend):** Python con Flask, en `app.py`. Toda la lógica (cálculos y reglas de negocio) va aquí, **NUNCA en la interfaz**.
- **Salón (frontend):** páginas HTML servidas por Flask, en `templates/`. Solo muestran información; no calculan ni deciden.

## Decisiones técnicas (acordadas)

- Lectura de Excel con **`pandas`** (sobre `openpyxl`); servidor web con **`Flask`**.
- Estructura: `app.py` (backend), `templates/` (HTML), `static/style.css` (diseño azul marino y dorado).
- Plan de implementación por fases: ver **`PLAN.md`**.

## Estado del repo

- **No hay código aún**: solo los insumos Excel en `Insumos/` y los documentos `AGENTS.md` y `PLAN.md`. No hay `requirements.txt`, `package.json`, tests, ni pistas.
- Sin sistema build/test/lint: verifica el trabajo ejecutando `python <script>.py` e inspeccionando la salida, gráficos o archivos generados.

## Archivos de entrada

- `Insumos/Maestro_Estudiantes.xlsx` → hoja `Estudiantes`: columnas `Identificacion`, `Nombre_Completo`, `Correo`, `Programa`, `Cohorte`. **24 estudiantes** (sin cabecera): 16 de `Técnico en IA Aplicada` y 8 de `Excel Avanzado para Negocios`, todos `Cohorte` `2026-A`. Nota: la cabecera real es `Identificacion` (sin tilde).
- `Insumos/Registro_Evaluaciones.xlsx` → hoja `Evaluaciones`: columnas `Identificacion`, `Programa`, `Modulo`, `Nota`, `Asistencia_Pct`, `Fecha_Cierre`. **88 filas**: el programa `Técnico en IA Aplicada` tiene 4 módulos (`Módulo 1`…`Módulo 4`); `Excel Avanzado para Negocios` tiene solo 3 (`Módulo 1`…`Módulo 3`).

## Casos borde conocidos y decisiones

- **`304560321` (Espinoza Leon Javier):** en el maestro, sin notas → mostrar "sin datos de evaluación", no genera certificado.
- **`999880777`:** 4 notas completas pero no existe en el maestro → generar su certificado marcado como incidencia "sin registro en maestro" (no hay nombre/correo).
- Promedio divide entre los **módulos cursados** (3 para Excel Avanzado, 4 para Técnico).
- Al codificar, normalizar identificaciones (`str(x).strip()`) por si llegan como texto o con espacios.

## Reglas de negocio

- **Promedio** = suma de `Nota` / cantidad de módulos cursados.
- **Asistencia** = promedio de `Asistencia_Pct`.
- Se agrupa por **`Identificacion` + `Programa`**: un certificado por estudiante y programa.
- **Aprobación** si `Promedio >= 70` y `Asistencia >= 80`.
- **Participación** si `Promedio < 70` y `Asistencia >= 80`.
- **Sin certificado** si `Asistencia < 80`.
- Los límites **incluyen** el valor (>=, <=). No redondear fuera de lo pedido sin avisar.

## Estilo de trabajo

- Código simple y **comentado en español**, señalando los "ladrillos" vistos en clase: variables, tipos, condicionales, bucles y funciones.
- Diseño web en **azul marino y dorado**.
- Explicar en español sencillo lo que se vaya haciendo.

## Convenciones (heredadas de la raíz)

- Scripts Python auxiliares de una sola tarea usan **prefijo de guion bajo**: `_validar_datos.py`, `_excel.py`, … Ejecutar con `python _scriptname.py`. La app web es la excepción: su backend vive en `app.py`.
- No hay manifiesto: instalar dependencias ad-hoc con `pip install` (herramientas ya presentes: `openpyxl`, `pandas`; `flask` se instala al trabajar el backend).
- Encoding: los acentos pueden verse como mojibake en la consola PowerShell por artefacto de codificación de la terminal; el contenido de los archivos (UTF-8) es correcto.

## Referencias

- `UniversidadFundepos/CLAUDE.md` — mapa de módulos y convenciones del programa (en español).
- `UniversidadFundepos/AGENTS.md` — estado del workspace y convenciones de scripting Python (patrón de scripts con prefijo `_`, autorización a `pip install`).
