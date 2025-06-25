from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file, make_response
from db import create_connection, close_connection, create_database
from dotenv import load_dotenv
import os
from mysql.connector import connect, Error
from datetime import datetime, timedelta
from typing import List
from functools import wraps
from dotenv import set_key

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache


@app.route('/', methods=['GET', 'POST'])
@nocache
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cfusuari WHERE coduser=%s AND clave=%s",
                (username, password)
            )
            user = cursor.fetchone()
            close_connection(conn)
            if user:
                session['user'] = username
                return redirect(url_for('clientes'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@nocache
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/clientes')
@nocache
def clientes():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = create_connection()
    clientes = []
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT TIPOCLI, NOMBRE, RIF, NIT, DIRECC1, DIRCORREO, NUMTEL FROM cfprocli")
        clientes = cursor.fetchall()
        close_connection(conn)
    return render_template('clientes.html', clientes=clientes)


@app.route('/configuracion', methods=['GET', 'POST'])
@nocache
def configuracion():
    mensaje = None
    # Leer configuración actual del entorno
    erp_tipo = os.getenv('ERP_TIPO', '')
    host = os.getenv('host', '')
    usuario = os.getenv('user', '')
    password = os.getenv('password', '')
    database = os.getenv('database', '')

    if request.method == 'POST':
        erp_tipo = request.form['erp_tipo']
        host = request.form['host']
        usuario = request.form['usuario']
        password = request.form['password']
        database = request.form['database']

        # Actualiza el archivo .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'ERP_TIPO', erp_tipo)
        set_key(env_path, 'host', host)
        set_key(env_path, 'user', usuario)
        set_key(env_path, 'password', password)
        set_key(env_path, 'database', database)

        # Recarga las variables de entorno
        load_dotenv(env_path, override=True)

        mensaje = "Configuración guardada correctamente."

    # Vuelve a leer la configuración después de guardar
    erp_tipo = os.getenv('ERP_TIPO', '')
    host = os.getenv('host', '')
    usuario = os.getenv('user', '')
    password = os.getenv('password', '')
    database = os.getenv('database', '')

    return render_template(
        'configuracion.html',
        mensaje=mensaje,
        erp_tipo=erp_tipo,
        host=host,
        usuario=usuario,
        database=database
    )

@app.route('/ventas', methods=['GET', 'POST'])
@nocache
def ventas():
    if 'user' not in session:
        return redirect(url_for('login'))



@app.route('/reportes', methods=['GET', 'POST'])
@nocache
def reportes():
    if 'user' not in session:
        return redirect(url_for('login'))

    # --- Filtros clientes ---
    filtro_rif = request.args.get('rif', '')
    filtro_nombre = request.args.get('nombre', '')
    filtro_email = request.args.get('dircorreo', '')

    query_clientes = "SELECT TIPOCLI, NOMBRE, RIF, NIT, DIRECC1, DIRCORREO, NUMTEL FROM cfprocli WHERE 1=1"
    params_clientes: List[str] = []

    if filtro_rif:
        query_clientes += " AND RIF LIKE %s"
        params_clientes.append(f"%{filtro_rif}%")
    if filtro_nombre:
        query_clientes += " AND NOMBRE LIKE %s"
        params_clientes.append(f"%{filtro_nombre}%")
    if filtro_email:
        query_clientes += " AND DIRCORREO LIKE %s"
        params_clientes.append(f"%{filtro_email}%")

    # --- Filtros ventas ---
    filtro_cufe = request.args.get('cufe', '')
    filtro_ruc = request.args.get('ruc', '')
    filtro_razon = request.args.get('razon_social', '')
    filtro_fecha = request.args.get('fecha', '')

    query_ventas = """
        SELECT NUMREF, TIPTRAN, feNroProtocolo, NOMBRE, RIF, MONTOBRU, FECEMISS, feResultado
        FROM dcheader
        WHERE 1=1
    """
    params_ventas = []

    if filtro_cufe:
        query_ventas += " AND feNroProtocolo LIKE %s"
        params_ventas.append(f"%{filtro_cufe}%")
    if filtro_ruc:
        query_ventas += " AND RIF LIKE %s"
        params_ventas.append(f"%{filtro_ruc}%")
    if filtro_razon:
        query_ventas += " AND NOMBRE LIKE %s"
        params_ventas.append(f"%{filtro_razon}%")
    if filtro_fecha:
        query_ventas += " AND DATE(FECEMISS) = %s"
        params_ventas.append(filtro_fecha)

    clientes = []
    empresa = {}
    ventas = []

    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        # Consulta de clientes
        cursor.execute(query_clientes, params_clientes)
        clientes = cursor.fetchall()
        # Consulta de empresa
        cursor.execute("SELECT nombre, numfiscal, direcc1, direcc2 FROM cfparame LIMIT 1")
        row = cursor.fetchone()
        if row:
            empresa = {
                'nombre': row[0],
                'numfiscal': row[1],
                'direccion': f"{row[2]} {row[3]}" if row[3] else row[2]
            }
        # Consulta de ventas
        cursor.execute(query_ventas, params_ventas)
        ventas = cursor.fetchall()
        close_connection(conn)

        usuario = session.get('user', 'Desconocido')
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')

                # --- Dashboard: últimos 3 meses ---
        hoy = datetime.now()
        primer_dia = (hoy.replace(day=1) - timedelta(days=60)).replace(day=1)
        fecha_inicio = primer_dia.strftime('%Y-%m-%d')

        # Ventas mensuales
        query_ventas_mes = """
            SELECT DATE_FORMAT(FECEMISS, '%%Y-%%m') as mes, SUM(MONTOBRU) as total
            FROM dcheader
            WHERE FECEMISS >= %s
            GROUP BY mes
            ORDER BY mes
        """
        # Ticket promedio mensual
        query_ticket = """
            SELECT IFNULL(SUM(MONTOBRU)/NULLIF(COUNT(*),0),0)
            FROM dcheader
            WHERE FECEMISS >= %s
        """
        # Clientes nuevos por mes
        query_clientes_mes = """
            SELECT DATE_FORMAT(fecha1s, '%%Y-%%m') as mes, COUNT(*) as total
            FROM cfprocli
            WHERE fecha1s >= %s
            GROUP BY mes
            ORDER BY mes
        """
        # Clientes nuevos total últimos 3 meses
        query_clientes_nuevos = """
            SELECT COUNT(*) FROM cfprocli WHERE fecha1s >= %s
        """

        dashboard = {
            "ventas_meses": [],
            "ventas_totales": [],
            "clientes_meses": [],
            "clientes_totales": [],
            "ticket_promedio": 0,
            "clientes_nuevos": 0
        }

        # ...código existente...

        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            # Ventas mensuales
            cursor.execute(query_ventas_mes, (fecha_inicio,))
            ventas_mes_result = cursor.fetchall()
            if ventas_mes_result:
                dashboard["ventas_meses"], dashboard["ventas_totales"] = zip(*ventas_mes_result)
            else:
                dashboard["ventas_meses"], dashboard["ventas_totales"] = [], []

            # Ticket promedio
            cursor.execute(query_ticket, (fecha_inicio,))
            ticket_result = cursor.fetchone()
            dashboard["ticket_promedio"] = float(ticket_result[0] or 0) if ticket_result else 0

            # Clientes nuevos por mes
            cursor.execute(query_clientes_mes, (fecha_inicio,))
            clientes_mes_result = cursor.fetchall()
            if clientes_mes_result:
                dashboard["clientes_meses"], dashboard["clientes_totales"] = zip(*clientes_mes_result)
            else:
                dashboard["clientes_meses"], dashboard["clientes_totales"] = [], []

            # Clientes nuevos total
            cursor.execute(query_clientes_nuevos, (fecha_inicio,))
            clientes_nuevos_result = cursor.fetchone()
            dashboard["clientes_nuevos"] = clientes_nuevos_result[0] if clientes_nuevos_result else 0

            close_connection(conn)


    return render_template(
        'reportes.html',
        clientes=clientes,
        filtro_rif=filtro_rif,
        filtro_nombre=filtro_nombre,
        filtro_email=filtro_email,
        empresa=empresa,
        usuario=usuario,
        fecha=fecha,
        ventas=ventas,
        filtro_cufe=filtro_cufe,
        filtro_ruc=filtro_ruc,
        filtro_razon=filtro_razon,
        filtro_fecha=filtro_fecha,
        dashboard=dashboard,
    

    )


@app.route('/guardar_cliente', methods=['POST'])
@nocache
def guardar_cliente():
    tipreg = 1
    tipocli = request.form['tipocli']
    nombre = request.form['nombre']
    rif = request.form['rif']
    nit = request.form['nit']
    direcc1 = request.form['direcc1']
    dircorreo = request.form['dircorreo']
    numtel = request.form['numtel']
    codigo = rif

    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM cfprocli WHERE TIPREG=%s AND TIPOCLI=%s AND CODIGO=%s",
            (tipreg, tipocli, codigo)
        )
        if cursor.fetchone():
            close_connection(conn)
            # Vuelve a cargar la página principal con el mensaje de error
            conn = create_connection()
            clientes = []
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT TIPOCLI, NOMBRE, RIF, NIT, DIRECC1, DIRCORREO, NUMTEL FROM cfprocli")
                clientes = cursor.fetchall()
                close_connection(conn)
            return render_template('index.html', clientes=clientes, mensaje="Ya existe un cliente con ese RUC.")
        cursor.execute(
            "INSERT INTO cfprocli (TIPREG, CODIGO, TIPOCLI, NOMBRE, RIF, NIT, DIRECC1, DIRCORREO, NUMTEL) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (tipreg, codigo, tipocli, nombre, rif, nit, direcc1, dircorreo, numtel)
        )
        conn.commit()
        close_connection(conn)
        flash("Cliente creado exitosamente.", "success")
    return redirect('/')


@app.route('/actualizar_cliente', methods=['POST'])
@nocache
def actualizar_cliente():
    cliente_id = request.form['cliente_id']
    tipocli = request.form['tipocli']
    nombre = request.form['nombre']
    rif = request.form['rif']
    nit = request.form['nit']
    direcc1 = request.form['direcc1']
    dircorreo = request.form['dircorreo']
    numtel = request.form['numtel']

    conn = create_connection()
    # ...código existente...
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cfprocli SET TIPOCLI=%s, NOMBRE=%s, RIF=%s, NIT=%s, DIRECC1=%s, DIRCORREO=%s, NUMTEL=%s WHERE id=%s",
            (tipocli, nombre, rif, nit, direcc1, dircorreo, numtel, cliente_id)
        )
        conn.commit()
        close_connection(conn)
# ...código existente...
    return redirect('/')

def init():
    print("Inicializando la aplicación...")
    conn = create_connection()
    if conn:
        print("Conexión a la base de datos establecida.")
        close_connection(conn)
    else:
        print("No se pudo establecer la conexión a la base de datos.")
    print("Aplicación inicializada correctamente.")
    conn = create_connection()
    if conn:
        print("Database connection established.")
        close_connection(conn)
    else:
        print("Failed to establish database connection.")
    
    print("Application initialized successfully.")

if __name__ == "__main__":
    init()
    app.run(debug=True)