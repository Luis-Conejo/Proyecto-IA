# app.py — LA COCINA: servidor web con Flask para la emision de certificados
# de Academia Horizonte. Reutiliza la logica validada en _validar_datos.py.
# El SALON (templates/ y static/) solo muestra informacion: no calcula ni decide.

# -*- coding: utf-8 -*-
import hashlib  # LADRILLO: LIBRERIA -> para guardar claves cifradas, nunca en texto plano
import json     # LADRILLO: LIBRERIA -> para guardar los usuarios en un archivo
import os       # LADRILLO: LIBRERIA -> para leer secretos de variables de entorno (Vercel)
from functools import wraps  # LADRILLO: LIBRERIA -> para crear el decorador de login
from pathlib import Path  # LADRILLO: PATHLIB -> rutas sin depender de donde se corra
import pandas as pd
from flask import Flask, abort, redirect, render_template, request, session, url_for

from _validar_datos import calcular_promedio, decidir_certificado, normalizar_id

# LADRILLO: VARIABLE -> creamos la aplicacion Flask
app = Flask(__name__)

# LADRILLO: VARIABLE -> clave secreta para firmar las sesiones (quien entra y quien no)
# En Vercel se configura como variable de entorno SECRET_KEY; en local usa este valor.
app.secret_key = os.environ.get("SECRET_KEY", "academia-horizonte-certificados-2026")

# LADRILLO: VARIABLES -> rutas de la Bodega (los Excel, solo lectura)
# Se construyen desde la carpeta de ESTE archivo, no desde la carpeta de trabajo
# actual: asi la app funciona al ejecutarla desde cualquier directorio.
CARPETA_APP = Path(__file__).resolve().parent
RUTA_MAESTRO = CARPETA_APP / "Insumos" / "Maestro_Estudiantes.xlsx"
RUTA_EVALUACIONES = CARPETA_APP / "Insumos" / "Registro_Evaluaciones.xlsx"

# ---------- AUTENTICACION: quien puede entrar (Cocina, regla de negocio) ----------
# LADRILLO: VARIABLE de TIPO diccionario -> el unico administrador.
# En Vercel se configura con las variables de entorno ADMIN_CORREO y ADMIN_CLAVE;
# en local usa estos valores por defecto. Es el ADMIN quien da acceso a los usuarios.
ADMIN = {
    "correo": os.environ.get("ADMIN_CORREO", "lconejomonge@gmail.com"),
    "clave": os.environ.get("ADMIN_CLAVE", "LUIS.CONEJO"),
}

# LADRILLO: VARIABLE -> archivo donde se guardan los usuarios creados por el admin
# En Vercel el disco es de solo lectura salvo /tmp, asi que ahi se guarda en /tmp.
if os.environ.get("VERCEL"):  # LADRILLO: CONDICIONAL -> estamos en Vercel
    RUTA_USUARIOS = Path("/tmp/usuarios.json")
else:
    RUTA_USUARIOS = CARPETA_APP / "usuarios.json"


# ---------- LADRILLO: FUNCIÓN (cifra una clave) ----------
def cifrar_clave(clave):
    """Devuelve la clave convertida en codigo irreconocible (hash).
    Asi el archivo de usuarios nunca guarda claves en texto plano."""
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


# ---------- LADRILLO: FUNCIÓN (lee los usuarios creados por el admin) ----------
def leer_usuarios():
    """Lee usuarios.json y devuelve un diccionario {correo: clave_cifrada}.
    Si el archivo aun no existe, devuelve un diccionario vacio."""
    if not RUTA_USUARIOS.exists():  # LADRILLO: CONDICIONAL
        return {}
    with open(RUTA_USUARIOS, encoding="utf-8") as archivo:
        return json.load(archivo)


# ---------- LADRILLO: FUNCIÓN (guarda un usuario nuevo) ----------
def guardar_usuario(correo, clave):
    """Agrega (o reemplaza) un usuario normal en usuarios.json con su clave cifrada."""
    usuarios = leer_usuarios()
    usuarios[correo.strip().lower()] = cifrar_clave(clave)
    with open(RUTA_USUARIOS, "w", encoding="utf-8") as archivo:
        json.dump(usuarios, archivo, ensure_ascii=False, indent=2)


# ---------- LADRILLO: FUNCIÓN (revisa si correo y clave son validos) ----------
def credenciales_validas(correo, clave):
    """Devuelve True si el correo existe y la clave coincide (admin o usuario normal)."""
    correo = correo.strip().lower()
    # LADRILLO: CONDICIONAL -> primero revisamos al administrador fijo
    if correo == ADMIN["correo"] and clave == ADMIN["clave"]:
        return True
    # LADRILLO: CONDICIONAL -> luego los usuarios creados por el admin
    usuarios = leer_usuarios()
    return correo in usuarios and usuarios[correo] == cifrar_clave(clave)


# ---------- LADRILLO: FUNCIÓN decoradora (el "portero" de las paginas) ----------
def requiere_login(vista):
    """Decorador: si no hay usuario en la sesion, manda a la pantalla de entrada."""
    @wraps(vista)
    def vista_protegida(*args, **kwargs):
        if "correo" not in session:  # LADRILLO: CONDICIONAL -> sin sesion, al login
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return vista_protegida


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
# ---------- Pantalla de entrada (login) ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Pantalla de entrada: pide correo y clave. Si son validos, abre sesion."""
    error = ""
    if request.method == "POST":  # LADRILLO: CONDICIONAL -> el usuario envio el formulario
        correo = request.form.get("correo", "")
        clave = request.form.get("clave", "")
        if credenciales_validas(correo, clave):  # LADRILLO: CONDICIONAL
            session["correo"] = correo.strip().lower()  # LADRILLO: VARIABLE -> sesion iniciada
            # El admin entra directo a su panel; los demas a los certificados
            if session["correo"] == ADMIN["correo"]:
                return redirect(url_for("admin"))
            return redirect(url_for("index"))
        error = "Correo o contraseña incorrectos."
    return render_template("login.html", error=error)


# ---------- Cerrar sesion ----------
@app.route("/logout")
def logout():
    """Cierra la sesion y regresa a la pantalla de entrada."""
    session.clear()
    return redirect(url_for("login"))


# ---------- Panel del administrador: aqui da acceso a usuarios normales ----------
@app.route("/admin", methods=["GET", "POST"])
@requiere_login
def admin():
    """Solo el admin: crea usuarios normales (correo + clave asignada) y los lista."""
    if session["correo"] != ADMIN["correo"]:  # LADRILLO: CONDICIONAL -> no es admin, fuera
        return redirect(url_for("index"))
    mensaje = ""
    if request.method == "POST":  # LADRILLO: CONDICIONAL -> el admin envio el formulario
        correo = request.form.get("correo", "").strip().lower()
        clave = request.form.get("clave", "")
        if correo and clave:  # LADRILLO: CONDICIONAL -> ambos campos con texto
            guardar_usuario(correo, clave)
            mensaje = f"Acceso creado para {correo}."
        else:
            mensaje = "Escribe correo y contraseña."
    return render_template("admin.html", usuarios=leer_usuarios(), mensaje=mensaje)


@app.route("/")
@requiere_login
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
@requiere_login
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
