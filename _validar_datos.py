# _validar_datos.py — Fase 1: validación del cruce de datos (solo lectura)
# Lee los dos Excel de Insumos/, cruza por Identificacion + Programa,
# calcula promedios y tipo de certificado, y reporta inconsistencias.
# Las funciones de este archivo las reutiliza app.py (la app web).

# -*- coding: utf-8 -*-
import pandas as pd

# ---------- LADRILLO: VARIABLES (rutas de los archivos de la Bodega) ----------
RUTA_MAESTRO = "Insumos/Maestro_Estudiantes.xlsx"
RUTA_EVALUACIONES = "Insumos/Registro_Evaluaciones.xlsx"


# ---------- LADRILLO: FUNCIÓN (normaliza la identificacion a texto) ----------
def normalizar_id(valor):
    """Convierte la identificacion a texto y le quita espacios."""
    return str(valor).strip()


# ---------- LADRILLO: FUNCIÓN (calcular_promedio) ----------
def calcular_promedio(valores):
    """Recibe una lista de numeros (TIPO: lista) y devuelve su promedio."""
    suma = 0.0  # LADRILLO: VARIABLE acumuladora, de TIPO float
    for numero in valores:  # LADRILLO: BUCLE for que recorre cada valor
        suma = suma + numero  # LADRILLO: VARIABLE que se actualiza
    return suma / len(valores)  # TIPO: el resultado es float


# ---------- LADRILLO: FUNCIÓN (decidir_certificado) ----------
def decidir_certificado(promedio, asistencia):
    """Decide el tipo de certificado segun las reglas de negocio del AGENTS.md."""
    if promedio >= 70 and asistencia >= 80:  # LADRILLO: CONDICIONAL -> Aprobacion
        return "Aprobacion"
    if promedio < 70 and asistencia >= 80:  # LADRILLO: CONDICIONAL -> Participacion
        return "Participacion"
    return "Sin certificado"  # Caso restante: Asistencia < 80


if __name__ == "__main__":
    # Bloque principal: solo se ejecuta al correr "python _validar_datos.py".
    # Cuando app.py importa este archivo, solo usa las funciones (sin imprimir).

    # ---------- 1. LECTURA de los dos Excel (Bodega, solo lectura) ----------
    print("== Leyendo insumos ==")
    df_maestro = pd.read_excel(RUTA_MAESTRO, sheet_name="Estudiantes")
    df_eval = pd.read_excel(RUTA_EVALUACIONES, sheet_name="Evaluaciones")

    # Normalizamos la identificacion en ambos archivos (puede llegar como texto o numero)
    df_maestro["id_norm"] = df_maestro["Identificacion"].map(normalizar_id)
    df_eval["id_norm"] = df_eval["Identificacion"].map(normalizar_id)

    # ---------- 2. RESUMEN general de los datos ----------
    print("\n== Resumen general ==")
    print("Estudiantes por programa (maestro):")
    print(df_maestro["Programa"].value_counts().to_string())
    print("\nCantidad de evaluaciones:", len(df_eval))
    print("Modulos existentes:", sorted(df_eval["Modulo"].unique()))
    print("Rango de notas (min-max):", df_eval["Nota"].min(), "-", df_eval["Nota"].max())
    print("Rango de asistencia (min-max):", df_eval["Asistencia_Pct"].min(), "-", df_eval["Asistencia_Pct"].max())

    # ---------- 3. CRUCE por Identificacion + Programa ----------
    # Diccionario del maestro: identificacion -> nombre (para la tabla)
    nombres = dict(zip(df_maestro["id_norm"], df_maestro["Nombre_Completo"]))

    # Agrupamos las evaluaciones por (identificacion, programa): un grupo = un certificado
    grupos = df_eval.groupby(["id_norm", "Programa"])

    # ---------- 4. CÁLCULO por estudiante: modulos, promedio, asistencia, tipo ----------
    filas = []  # LADRILLO: VARIABLE de TIPO lista, guardara una fila por estudiante
    for (identificacion, programa), grupo in grupos:  # LADRILLO: BUCLE for sobre los grupos
        modulos_cursados = len(grupo)  # Cantidad de filas del grupo = modulos cursados
        promedio = calcular_promedio(grupo["Nota"].tolist())  # LADRILLO: uso de la FUNCION
        asistencia_prom = calcular_promedio(grupo["Asistencia_Pct"].tolist())
        tipo = decidir_certificado(promedio, asistencia_prom)  # LADRILLO: uso de la FUNCION

        nombre = nombres.get(identificacion, "SIN REGISTRO EN MAESTRO")
        filas.append({  # LADRILLO: VARIABLE de TIPO diccionario
            "Identificacion": identificacion,
            "Nombre": nombre,
            "Programa": programa,
            "Modulos cursados": modulos_cursados,
            "Promedio": round(promedio, 2),  # Redondeo SOLO para mostrarlo en pantalla
            "Asistencia promedio": round(asistencia_prom, 2),
            "Tipo de certificado": tipo,
        })

    df_resultado = pd.DataFrame(filas)  # LADRILLO: VARIABLE de TIPO DataFrame

    # ---------- 5. TABLA completa ordenada por programa y nombre ----------
    df_tabla = df_resultado.sort_values(["Programa", "Nombre"]).reset_index(drop=True)
    print("\n== Tabla de certificados (ordenada por programa y nombre) ==")
    print(df_tabla.to_string(index=False))

    # Resumen de tipos (control de calidad contra el analisis previo)
    print("\n== Resumen por tipo de certificado ==")
    print(df_tabla["Tipo de certificado"].value_counts().to_string())

    # ---------- 6. INCONSISTENCIAS del cruce ----------
    ids_maestro = set(df_maestro["id_norm"])
    ids_eval = set(df_eval["id_norm"])

    print("\n== Inconsistencias ==")
    # a) Estudiantes del maestro SIN ninguna evaluacion
    sin_eval = df_maestro[~df_maestro["id_norm"].isin(ids_eval)]
    if len(sin_eval) == 0:
        print("- Ningun estudiante del maestro esta sin evaluaciones.")
    else:
        print("- Estudiantes del maestro SIN evaluaciones:")
        print(sin_eval[["id_norm", "Nombre_Completo", "Programa"]].to_string(index=False))

    # b) Identificaciones en evaluaciones que NO estan en el maestro
    sin_maestro = df_eval[~df_eval["id_norm"].isin(ids_maestro)]
    if len(sin_maestro) == 0:
        print("- Ninguna evaluacion referencia a un estudiante fuera del maestro.")
    else:
        print("- Evaluaciones con identificacion que NO existe en el maestro:")
        resumen = (
            sin_maestro.groupby("id_norm")
            .agg(Notas_registradas=("Nota", "count"), Programa=("Programa", "first"))
            .reset_index()
        )
        print(resumen.to_string(index=False))

    # ---------- Cierre ----------
    print("\nValidacion completada. Total de certificados calculados:", len(df_tabla))
