import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psycopg2
from typing import Dict, List, Tuple

class ComentariosGUI:

    def __init__(self, host: str, port: str, database: str, user: str, password: str, schema: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.schema = schema
        self.conn = None
        self.cursor = None
        self.tablas_datos = {}  
        self.widgets_comentarios = {}  

        self.root = tk.Tk()
        self.root.title(f"Agregar Comentarios - {schema} @ {database}")
        self.root.geometry("1200x600")

        self.conectar_bd()
        self.crear_interfaz()
        self.cargar_tablas()



    def conectar_bd(self):

        """Conecta a la base de datos PostgreSQL"""

        try:

            self.conn = psycopg2.connect(

                host=self.host,

                port=self.port,

                database=self.database,

                user=self.user,

                password=self.password

            )

            self.conn.autocommit = True

            self.cursor = self.conn.cursor()

            print(f"Conexión exitosa a {self.database}")

        except Exception as e:

            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos:\n{e}")

            sys.exit(1)



    def crear_interfaz(self):
        """Crea la interfaz gráfica principal"""
        info_frame = ttk.Frame(self.root, padding="10")
        info_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(info_frame, text=f"Base de datos: {self.database}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, text=f"Esquema: {self.schema}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(btn_frame, text="💾 Guardar Todos los Comentarios", command=self.guardar_todos_comentarios).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Recargar", command=self.recargar_datos).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cerrar", command=self.cerrar).pack(side=tk.RIGHT, padx=5)
        # Notebook (pestañas) para las tablas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def cargar_tablas(self):
        """Carga todas las tablas del esquema"""
        try:
            sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
            self.cursor.execute(sql, (self.schema,))
            tablas = [row[0] for row in self.cursor.fetchall()]
            if not tablas:
                messagebox.showwarning("Sin Tablas", f"No se encontraron tablas en el esquema '{self.schema}'")
                self.cerrar()
                return
            print(f"✓ Se encontraron {len(tablas)} tablas")
            # Crear una pestaña por cada tabla
            for tabla in tablas:
                self.crear_pestana_tabla(tabla)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar tablas:\n{e}")
            self.cerrar()

    def crear_pestana_tabla(self, tabla: str):
        """Crea una pestaña para una tabla específica"""
        # Obtener campos de la tabla
        campos_info = self.obtener_campos_tabla(tabla)
        if not campos_info:
            return
        self.tablas_datos[tabla] = campos_info
        # Crear frame para la pestaña
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=tabla)
        # Crear canvas y scrollbar para scroll vertical
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(header_frame, text=f"Tabla: {tabla}", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="💾 Guardar Comentarios de esta Tabla",
                  command=lambda t=tabla: self.guardar_comentarios_tabla(t)).pack(side=tk.RIGHT, padx=5)
        # Grid con campos
        grid_frame = ttk.Frame(scrollable_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # Headers del grid
        ttk.Label(grid_frame, text="Campo", font=('Arial', 10, 'bold'), width=25, anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(grid_frame, text="Tipo de Dato", font=('Arial', 10, 'bold'), width=20, anchor='w').grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(grid_frame, text="Comentario", font=('Arial', 10, 'bold'), width=60, anchor='w').grid(row=0, column=2, padx=5, pady=5, sticky='w')
        # Agregar separador
        ttk.Separator(grid_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        # Crear campos editables
        for idx, (campo, tipo, comentario_actual) in enumerate(campos_info, start=2):
            # Nombre del campo
            ttk.Label(grid_frame, text=campo, width=25, anchor='w').grid(row=idx, column=0, padx=5, pady=5, sticky='w')
            # Tipo de dato
            ttk.Label(grid_frame, text=tipo, width=20, anchor='w', foreground='gray').grid(row=idx, column=1, padx=5, pady=5, sticky='w')
            # Text widget para comentario (multilinea con altura fija)
            text_widget = tk.Text(grid_frame, width=60, height=2, wrap=tk.WORD, font=('Arial', 9))
            text_widget.grid(row=idx, column=2, padx=5, pady=5, sticky='ew')
            # Insertar comentario actual si existe
            if comentario_actual:
                text_widget.insert('1.0', comentario_actual)
            # Guardar referencia al widget
            self.widgets_comentarios[(tabla, campo)] = text_widget
        # Pack canvas y scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)



        # Habilitar scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def obtener_campos_tabla(self, tabla: str) -> List[Tuple[str, str, str]]:
        """Obtiene información de campos de una tabla"""
        sql = """

        SELECT

            c.column_name,

            CASE

                WHEN c.udt_name = 'date' THEN 'date'

                WHEN c.udt_name = 'timestamp' THEN 'timestamp'

                WHEN c.udt_name = 'int8' THEN 'bigint'

                WHEN c.udt_name = 'int4' THEN 'integer'

                WHEN c.udt_name = 'int2' THEN 'smallint'

                WHEN c.udt_name = 'text' THEN 'text'

                WHEN c.udt_name = 'numeric' THEN 'numeric'

                WHEN c.udt_name = 'jsonb' THEN 'jsonb'

                WHEN c.udt_name IN ('bpchar', 'varchar') THEN

                    'varchar(' || COALESCE(c.character_maximum_length, 255)::text || ')'

                WHEN c.character_maximum_length IS NOT NULL THEN

                    c.udt_name || '(' || c.character_maximum_length || ')'

                ELSE c.udt_name

            END AS tipo_dato,

            COALESCE(pgd.description, '') AS comentario

        FROM information_schema.columns c

        LEFT JOIN pg_catalog.pg_description pgd ON (

            pgd.objoid = (

                SELECT c_table.oid

                FROM pg_catalog.pg_class c_table

                WHERE c_table.relname = c.table_name

                  AND c_table.relnamespace = (

                      SELECT n.oid

                      FROM pg_catalog.pg_namespace n

                      WHERE n.nspname = c.table_schema

                  )

            )

            AND pgd.objsubid = c.ordinal_position

        )

        WHERE c.table_schema = %s

          AND c.table_name = %s

        ORDER BY c.ordinal_position;

        """



        try:

            self.cursor.execute(sql, (self.schema, tabla))

            return [(row[0], row[1], row[2]) for row in self.cursor.fetchall()]

        except Exception as e:

            print(f"Error al obtener campos de {tabla}: {e}")

            return []



    def guardar_comentarios_tabla(self, tabla: str):

        """Guarda los comentarios de una tabla específica"""

        try:

            campos_modificados = 0



            for campo, tipo, comentario_original in self.tablas_datos[tabla]:

                widget = self.widgets_comentarios.get((tabla, campo))

                if not widget:

                    continue



                # Obtener el nuevo comentario del widget

                nuevo_comentario = widget.get('1.0', tk.END).strip()



                # Solo actualizar si cambió

                if nuevo_comentario != comentario_original:

                    self.aplicar_comentario(tabla, campo, nuevo_comentario)

                    campos_modificados += 1



            if campos_modificados > 0:

                messagebox.showinfo("Éxito", f"Se guardaron {campos_modificados} comentarios en la tabla '{tabla}'")

            else:

                messagebox.showinfo("Sin Cambios", f"No hay comentarios nuevos o modificados en la tabla '{tabla}'")



        except Exception as e:

            messagebox.showerror("Error", f"Error al guardar comentarios de '{tabla}':\n{e}")



    def guardar_todos_comentarios(self):

        """Guarda todos los comentarios de todas las tablas"""

        try:

            total_modificados = 0



            for tabla in self.tablas_datos:

                for campo, tipo, comentario_original in self.tablas_datos[tabla]:

                    widget = self.widgets_comentarios.get((tabla, campo))

                    if not widget:

                        continue



                    # Obtener el nuevo comentario del widget

                    nuevo_comentario = widget.get('1.0', tk.END).strip()



                    # Solo actualizar si cambió

                    if nuevo_comentario != comentario_original:

                        self.aplicar_comentario(tabla, campo, nuevo_comentario)

                        total_modificados += 1



            if total_modificados > 0:

                messagebox.showinfo("Éxito", f"Se guardaron {total_modificados} comentarios en total")

                self.recargar_datos()

            else:

                messagebox.showinfo("Sin Cambios", "No hay comentarios nuevos o modificados")



        except Exception as e:

            messagebox.showerror("Error", f"Error al guardar comentarios:\n{e}")



    def aplicar_comentario(self, tabla: str, campo: str, comentario: str):

        """Aplica un comentario a un campo específico"""

        try:

            if comentario:

                sql = f"""

                COMMENT ON COLUMN {self.schema}.{tabla}.{campo} IS %s;

                """

                self.cursor.execute(sql, (comentario,))

            else:

                # Si el comentario está vacío, eliminarlo

                sql = f"""

                COMMENT ON COLUMN {self.schema}.{tabla}.{campo} IS NULL;

                """

                self.cursor.execute(sql)



            print(f"✓ Comentario actualizado: {tabla}.{campo}")



        except Exception as e:

            print(f"✗ Error al actualizar comentario de {tabla}.{campo}: {e}")

            raise



    def recargar_datos(self):

        """Recarga los datos desde la base de datos"""

        # Limpiar notebook

        for tab in self.notebook.tabs():

            self.notebook.forget(tab)



        # Limpiar estructuras de datos

        self.tablas_datos.clear()

        self.widgets_comentarios.clear()



        # Recargar

        self.cargar_tablas()



        messagebox.showinfo("Recargado", "Los datos se han recargado correctamente")



    def cerrar(self):

        """Cierra la conexión y la ventana"""

        if self.cursor:

            self.cursor.close()

        if self.conn:

            self.conn.close()

        self.root.quit()

        self.root.destroy()



    def ejecutar(self):

        """Ejecuta el loop principal de la GUI"""

        try:

            self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

            self.root.mainloop()

        except Exception as e:

            # Si la ventana ya fue destruida, ignorar el error

            if "application has been destroyed" not in str(e):

                raise



def main():

    # Configurar codificación UTF-8 para la consola

    import builtins

    try:

        sys.stdout.reconfigure(encoding='utf-8')

        sys.stderr.reconfigure(encoding='utf-8')

    except:

        # Fallback: envolver print para evitar errores de codificación

        _orig_print = builtins.print

        def _safe_print(*args, **kwargs):

            try:

                _orig_print(*args, **kwargs)

            except UnicodeEncodeError:

                file = kwargs.get('file', sys.stdout)

                sep = kwargs.get('sep', ' ')

                end = kwargs.get('end', '\n')

                text = sep.join(str(a) for a in args) + end

                enc = getattr(file, 'encoding', None) or 'utf-8'

                try:

                    if hasattr(file, 'buffer'):

                        file.buffer.write(text.encode(enc, errors='replace'))

                    else:

                        file.write(text.encode(enc, errors='replace').decode(enc))

                except:

                    _orig_print(text.encode('utf-8', errors='replace').decode('utf-8'))

        builtins.print = _safe_print



    if len(sys.argv) != 7:

        print("Error: Se requieren 6 parametros")

        print("Uso: python agregar_comentarios.py <host> <puerto> <bd> <usuario> <password> <esquema>")

        sys.exit(1)



    host = sys.argv[1]

    puerto = sys.argv[2]

    bd = sys.argv[3]

    usuario = sys.argv[4]

    password = sys.argv[5]

    esquema = sys.argv[6]



    print(f"Iniciando interfaz de comentarios...")

    print(f"Host: {host}")

    print(f"Puerto: {puerto}")

    print(f"Base de datos: {bd}")

    print(f"Usuario: {usuario}")

    print(f"Esquema: {esquema}")



    try:

        app = ComentariosGUI(host, puerto, bd, usuario, password, esquema)

        app.ejecutar()

        print("\nAplicacion cerrada correctamente")

    except Exception as e:

        print(f"\nError fatal: {e}")

        import traceback

        traceback.print_exc()

        sys.exit(1)





if __name__ == "__main__":

    main()

