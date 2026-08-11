# app.py — LA COCINA: servidor web con Flask para la emision de certificados
# de Academia Horizonte. Reutiliza la logica validada en _validar_datos.py.
# El SALON (templates/ y static/) solo muestra informacion: no calcula ni decide.

# -*- coding: utf-8 -*-
import pandas as pd
from flask import Flask, abort, render_template, request

from _validar_datos import calcular_promedio, decidir_certificado, normalizar_id

# LADRILLO: VARIABLE -> creamos la aplicacion Flask
app = Flask(__name__)

# LADRILLO: VARIABLES -> rutas de la Bodega (los Excel, solo lectura)
RUTA_MAESTRO = "Insumos/Maestro_Estudiantes.xlsx"
RUTA_EVALUACIONES = "Insumos/Registro_Evaluaciones.xlsx"


# ---------- LADRILLO: FUNCIÓN (lee los dos Excel) ----------
def leer_datos():
    """Lee la Bodega y devuelve dos DataFrames con la identificacion normalizada."""
    df_maestro = pd.read_excel(RUTA_MAESTRO, sheet_name="Estudiantes")
    df_eval = pd.read_excel(RUTA_EVALUACIONES, sheet_name="Evaluaciones")
    # Normalizamos los ids (pueden llegar como texto o numero, con o sin espacios)
    df_maestro["id_norm"] = df_maestro["Identificacion"].map(normalizar_id)
    df_eval["id_norm"] = df_eval["Identificacion"].map(normalizar_id)
    return df_maestro, df_eval


# ---------- LADRILLO: FUNCIÓN (cruza los datos y calcula todo) ----------
def calcular_resultados(df_maestro, df_eval):
    """Cruza por Identificacion + Programa y devuelve:
    - certificados: un dict por estudiante (los emitibles y los que no),
    - inconsistencias: las 3 detectadas en la Fase 1,
    - conteos: totales por tipo de certificado (solo emitibles)."""

    # Diccionarios del maestro para completar datos del estudiante
    nombres = dict(zip(df_maestro["id_norm"], df_maestro["Nombre_Completo"]))
    correos = dict(zip(df_maestro["id_norm"], df_maestro["Correo"]))
    cohortes = dict(zip(df_maestro["id_norm"], df_maestro["Cohorte"]))

    certificados = []  # LADRILLO: VARIABLE de TIPO lista (un dict por grupo)
    # LADRILLO: BUCLE for -> un grupo de evaluaciones por (identificacion, programa)
    for (identificacion, programa), grupo in df_eval.groupby(["id_norm", "Programa"]):
        modulos = len(grupo)  # Modulos cursados = filas del grupo
        promedio = calcular_promedio(grupo["Nota"].tolist())  # LADRILLO: FUNCION reutilizada
        asistencia = calcular_promedio(grupo["Asistencia_Pct"].tolist())
        tipo = decidir_certificado(promedio, asistencia)  # LADRILLO: FUNCION reutilizada

        en_maestro = identificacion in nombres
        certificados.append({  # LADRILLO: VARIABLE de TIPO diccionario
            "identificacion": identificacion,
            "nombre": nombres.get(identificacion, "SIN REGISTRO EN MAESTRO"),
            "correo": correos.get(identificacion, ""),
            "programa": programa,
            "cohorte": cohortes.get(identificacion, ""),
            "modulos": modulos,
            "promedio": round(promedio, 2),  # Redondeo solo para mostrar
            "asistencia": round(asistencia, 2),
            "tipo": tipo,
            "emitible": en_maestro,  # LADRILLO: CONDICIONAL -> booleano
        })

    # ---------- INCONSISTENCIAS (las 3 detectadas en la Fase 1) ----------
    inconsistencias = []  # LADRILLO: VARIABLE de TIPO lista
    ids_maestro = set(df_maestro["id_norm"])
    ids_eval = set(df_eval["id_norm"])

    # 1) Estudiante del maestro SIN ninguna evaluacion
    sin_eval = df_maestro[~df_maestro["id_norm"].isin(ids_eval)]
    for _, fila in sin_eval.iterrows():  # LADRILLO: BUCLE for
        inconsistencias.append({
            "tipo": "Sin evaluaciones",
            "detalle": "Aparece en el maestro pero no tiene notas registradas; no genera certificado.",
            "identificacion": fila["id_norm"],
            "nombre": fila["Nombre_Completo"],
            "programa": fila["Programa"],
        })

    # 2) Con evaluaciones completas pero SIN registro en el maestro
    for c in certificados:  # LADRILLO: BUCLE for
        if not c["emitible"]:  # LADRILLO: CONDICIONAL
            inconsistencias.append({
                "tipo": "Sin registro en maestro",
                "detalle": "Tiene notas completas pero no existe en el maestro; sin nombre ni correo, el certificado no se emite.",
                "identificacion": c["identificacion"],
                "nombre": c["nombre"],
                "programa": c["programa"],
                "promedio": c["promedio"],
                "asistencia": c["asistencia"],
            })

    # 3) Certificado no emitido por asistencia insuficiente
    for c in certificados:  # LADRILLO: BUCLE for
        if c["emitible"] and c["tipo"] == "Sin certificado":  # LADRILLO: CONDICIONAL
            inconsistencias.append({
                "tipo": "Asistencia insuficiente",
                "detalle": "Asistencia promedio menor a 80; no recibe certificado.",
                "identificacion": c["identificacion"],
                "nombre": c["nombre"],
                "programa": c["programa"],
                "promedio": c["promedio"],
                "asistencia": c["asistencia"],
            })

    # ---------- CONTADORES de la pagina (solo certificados emitibles) ----------
    conteos = {  # LADRILLO: VARIABLE de TIPO diccionario
        "aprobacion": sum(1 for c in certificados if c["emitible"] and c["tipo"] == "Aprobacion"),
        "participacion": sum(1 for c in certificados if c["emitible"] and c["tipo"] == "Participacion"),
        "sin_certificado": sum(1 for c in certificados if c["emitible"] and c["tipo"] == "Sin certificado"),
    }

    return certificados, inconsistencias, conteos


# ---------- LADRILLO: rutas del servidor (la Cocina) ----------
@app.route("/")
def index():
    """Pagina principal: contadores, filtro por programa y tabla de certificados."""
    df_maestro, df_eval = leer_datos()
    certificados, inconsistencias, conteos = calcular_resultados(df_maestro, df_eval)

    # Programas disponibles (los dos del maestro) para el filtro
    programas = sorted(df_maestro["Programa"].unique())

    # Filtro por programa elegido en la pagina (GET /?programa=...)
    filtro = request.args.get("programa", "Todos")
    if filtro == "Todos":  # LADRILLO: CONDICIONAL
        visibles = [c for c in certificados if c["emitible"]]
    else:
        visibles = [c for c in certificados if c["emitible"] and c["programa"] == filtro]

    return render_template(
        "index.html",
        certificados=visibles,
        totales=conteos,
        inconsistencias=inconsistencias,
        programas=programas,
        filtro=filtro,
    )


@app.route("/certificado/<identificacion>")
def certificado(identificacion):
    """Ficha de un estudiante; devuelve 404 si la identificacion no existe."""
    df_maestro, df_eval = leer_datos()
    certificados, _, _ = calcular_resultados(df_maestro, df_eval)
    buscado = normalizar_id(identificacion)
    for c in certificados:  # LADRILLO: BUCLE for + CONDICIONAL
        if c["identificacion"] == buscado:
            return render_template("certificado.html", c=c)
    abort(404)


if __name__ == "__main__":
    # Arranca el servidor en http://localhost:5000
    # (activa debug=True mientras desarrollas; el .bat lo deja en False)
    app.run(host="127.0.0.1", port=5000, debug=False)
