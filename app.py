"""
Clínica Veterinaria Patitas - Sistema de citas
Flask + SQLite | Hecho por Marlene · UACJ
"""
import csv
import io
import os
import sqlite3
from functools import wraps

from flask import (Flask, Response, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "veterinaria.db")
IMG_DIR = os.path.join(BASE_DIR, "static", "img")
EXTENSIONES = {"jpg", "jpeg", "png", "webp"}

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-secreta-2026"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # fotos de máximo 5 MB

TIPOS = ["Perro", "Gato", "Conejo", "Hámster", "Ave", "Tortuga", "Otro"]
SERVICIOS = ["Consulta general", "Vacunación", "Desparasitación", "Baño y corte",
             "Cirugía", "Limpieza dental", "Revisión de seguimiento"]

# ---------------- Base de datos ----------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            foto TEXT NOT NULL,
            tipo TEXT NOT NULL,
            servicio TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            costo REAL NOT NULL
        );
    """)
    # Dos empleados por turno (contraseñas guardadas como hash, nunca en texto plano)
    if db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO usuarios (usuario, nombre, password_hash) VALUES (?, ?, ?)",
            [("cristina", "Cristina", generate_password_hash("Patitas123")),
             ("daniel", "Daniel", generate_password_hash("Huellitas456"))])
    # 10 pacientes ya registrados en la clínica
    if db.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO pacientes (nombre, foto, tipo, servicio, fecha, hora, costo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [("Max", "perro1.jpg", "Perro", "Vacunación", "2026-10-07", "09:00", 450),
             ("Luna", "gato1.jpg", "Gato", "Consulta general", "2026-10-07", "10:30", 350),
             ("Rocky", "perro2.jpg", "Perro", "Baño y corte", "2026-10-07", "12:00", 300),
             ("Michi", "gato2.jpg", "Gato", "Desparasitación", "2026-10-08", "09:30", 250),
             ("Copo", "conejo.jpg", "Conejo", "Revisión de seguimiento", "2026-10-08", "11:00", 280),
             ("Bella", "perro3.jpg", "Perro", "Cirugía", "2026-10-08", "16:00", 2500),
             ("Nina", "hamster.jpg", "Hámster", "Consulta general", "2026-10-09", "10:00", 200),
             ("Kiwi", "loro.jpg", "Ave", "Consulta general", "2026-10-09", "12:30", 320),
             ("Tito", "tortuga.jpg", "Tortuga", "Revisión de seguimiento", "2026-10-10", "09:00", 260),
             ("Simba", "gato3.jpg", "Gato", "Limpieza dental", "2026-10-10", "13:00", 900)])
    db.commit()
    db.close()


# ---------------- Seguridad ----------------

def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Inicia sesión para continuar.", "error")
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura


def guardar_foto(archivo):
    """Guarda la foto subida en static/img y devuelve su nombre, o None."""
    if not archivo or archivo.filename == "":
        return None
    ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if ext not in EXTENSIONES:
        return None
    nombre = secure_filename(archivo.filename)
    base, extension = os.path.splitext(nombre)
    i = 1
    while os.path.exists(os.path.join(IMG_DIR, nombre)):  # evita sobrescribir fotos
        nombre = f"{base}_{i}{extension}"
        i += 1
    archivo.save(os.path.join(IMG_DIR, nombre))
    return nombre


def leer_formulario():
    f = request.form
    datos = {k: f.get(k, "").strip() for k in ("nombre", "tipo", "servicio", "fecha", "hora", "costo")}
    if not all(datos.values()):
        return None, "Todos los campos son obligatorios."
    try:
        datos["costo"] = float(datos["costo"])
        if datos["costo"] < 0:
            raise ValueError
    except ValueError:
        return None, "El costo debe ser un número positivo."
    return datos, None


# ---------------- Rutas ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip().lower()
        password = request.form.get("password", "")
        fila = get_db().execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        if fila and check_password_hash(fila["password_hash"], password):
            session.clear()
            session["usuario_id"] = fila["id"]
            session["nombre"] = fila["nombre"]
            return redirect(url_for("inicio"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "ok")
    return redirect(url_for("login"))


@app.route("/")
@login_requerido
def inicio():
    q = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "")
    sql = "SELECT * FROM pacientes WHERE 1=1"
    params = []
    if q:
        sql += " AND (nombre LIKE ? OR servicio LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if tipo:
        sql += " AND tipo = ?"
        params.append(tipo)
    sql += " ORDER BY fecha, hora"
    pacientes = get_db().execute(sql, params).fetchall()
    destacados = get_db().execute("SELECT * FROM pacientes ORDER BY id LIMIT 6").fetchall()
    return render_template("inicio.html", pacientes=pacientes, destacados=destacados,
                           q=q, tipo=tipo, tipos=TIPOS)


@app.route("/paciente/<int:pid>")
@login_requerido
def ficha(pid):
    p = get_db().execute("SELECT * FROM pacientes WHERE id = ?", (pid,)).fetchone()
    if p is None:
        flash("Paciente no encontrado.", "error")
        return redirect(url_for("inicio"))
    return render_template("ficha.html", p=p)


@app.route("/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo():
    if request.method == "POST":
        datos, error = leer_formulario()
        foto = guardar_foto(request.files.get("foto"))
        if not error and not foto:
            error = "Sube una fotografía válida (jpg, jpeg, png o webp)."
        if error:
            flash(error, "error")
            return render_template("formulario.html", p=request.form, tipos=TIPOS,
                                   servicios=SERVICIOS, modo="nuevo")
        db = get_db()
        cur = db.execute(
            "INSERT INTO pacientes (nombre, foto, tipo, servicio, fecha, hora, costo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datos["nombre"], foto, datos["tipo"], datos["servicio"],
             datos["fecha"], datos["hora"], datos["costo"]))
        db.commit()
        flash(f"Paciente {datos['nombre']} registrado.", "ok")
        return redirect(url_for("ficha", pid=cur.lastrowid))
    return render_template("formulario.html", p={}, tipos=TIPOS, servicios=SERVICIOS, modo="nuevo")


@app.route("/paciente/<int:pid>/editar", methods=["GET", "POST"])
@login_requerido
def editar(pid):
    db = get_db()
    p = db.execute("SELECT * FROM pacientes WHERE id = ?", (pid,)).fetchone()
    if p is None:
        return redirect(url_for("inicio"))
    if request.method == "POST":
        datos, error = leer_formulario()
        if error:
            flash(error, "error")
            return render_template("formulario.html", p=p, tipos=TIPOS,
                                   servicios=SERVICIOS, modo="editar")
        foto = guardar_foto(request.files.get("foto")) or p["foto"]
        db.execute(
            "UPDATE pacientes SET nombre=?, foto=?, tipo=?, servicio=?, fecha=?, hora=?, costo=? "
            "WHERE id=?",
            (datos["nombre"], foto, datos["tipo"], datos["servicio"],
             datos["fecha"], datos["hora"], datos["costo"], pid))
        db.commit()
        flash("Cambios guardados.", "ok")
        return redirect(url_for("ficha", pid=pid))
    return render_template("formulario.html", p=p, tipos=TIPOS, servicios=SERVICIOS, modo="editar")


@app.route("/paciente/<int:pid>/eliminar", methods=["POST"])
@login_requerido
def eliminar(pid):
    db = get_db()
    db.execute("DELETE FROM pacientes WHERE id = ?", (pid,))
    db.commit()
    flash("Paciente eliminado.", "ok")
    return redirect(url_for("inicio"))


@app.route("/exportar")
@login_requerido
def exportar():
    filas = get_db().execute("SELECT * FROM pacientes ORDER BY fecha, hora").fetchall()
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["ID", "Nombre", "Tipo de animal", "Servicio", "Fecha", "Hora", "Costo", "Fotografía"])
    for f in filas:
        escritor.writerow([f["id"], f["nombre"], f["tipo"], f["servicio"],
                           f["fecha"], f["hora"], f"{f['costo']:.2f}", f["foto"]])
    # utf-8-sig agrega BOM para que Excel muestre bien acentos y la ñ
    contenido = salida.getvalue().encode("utf-8-sig")
    return Response(contenido, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=pacientes_veterinaria.csv"})


init_db()

if __name__ == "__main__":
    app.run(debug=True)
