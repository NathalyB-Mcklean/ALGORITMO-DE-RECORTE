import matplotlib.pyplot as plt
from matplotlib.widgets import Button


# 1. Estructura de datos: vertice de una lista doblemente enlazada
class Vertex:
    def __init__(self, x, y, intersect=False, entry=True, alpha=0.0):
        self.x = x
        self.y = y
        self.next = None
        self.prev = None
        self.nextPoly = None
        self.intersect = intersect
        self.entry = entry
        self.neighbour = None
        self.alpha = alpha
        self.visited = False

    def point(self):
        return (self.x, self.y)


class Polygon:
    def __init__(self):
        self.first = None

    def add(self, x, y):
        v = Vertex(x, y)
        if self.first is None:
            self.first = v
            v.next = v
            v.prev = v
        else:
            last = self.first.prev
            last.next = v
            v.prev = last
            v.next = self.first
            self.first.prev = v
        return v

    def insert_vertex(self, v, start, end):
        curr = start
        while curr != end and curr.alpha < v.alpha:
            curr = curr.next
        v.next = curr
        v.prev = curr.prev
        v.prev.next = v
        curr.prev = v

    def points(self):
        pts = []
        curr = self.first
        if curr is None:
            return pts
        while True:
            pts.append((curr.x, curr.y))
            curr = curr.next
            if curr is self.first:
                break
        return pts

    def first_unprocessed(self):
        curr = self.first
        while True:
            if curr.intersect and not curr.visited:
                return curr
            curr = curr.next
            if curr is self.first:
                return None


# 2. Funciones geometricas auxiliares
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segment_intersect(p1, p2, q1, q2):
    d1 = cross(q1, q2, p1)
    d2 = cross(q1, q2, p2)
    d3 = cross(p1, p2, q1)
    d4 = cross(p1, p2, q2)

    if d1 * d2 < 0 and d3 * d4 < 0:
        alphaP = d1 / (d1 - d2)
        alphaQ = d3 / (d3 - d4)
        return alphaP, alphaQ
    return None


def point_in_polygon(point, poly_points):
    x, y = point
    n = len(poly_points)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly_points[i]
        xj, yj = poly_points[j]
        if ((yi > y) != (yj > y)) and \
           (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


# 3. Fase 1: busqueda e insercion de intersecciones
def phase_one(subject, clip):
    s_points = subject.points()
    c_points = clip.points()
    ns, nc = len(s_points), len(c_points)

    s_vertices, curr = [], subject.first
    for _ in range(ns):
        s_vertices.append(curr)
        curr = curr.next

    c_vertices, curr = [], clip.first
    for _ in range(nc):
        c_vertices.append(curr)
        curr = curr.next

    any_intersection = False

    for i in range(ns):
        s1, s2 = s_vertices[i], s_vertices[(i + 1) % ns]
        for j in range(nc):
            c1, c2 = c_vertices[j], c_vertices[(j + 1) % nc]
            result = segment_intersect(s1.point(), s2.point(),
                                        c1.point(), c2.point())
            if result is not None:
                alphaP, alphaQ = result
                ix = s1.x + alphaP * (s2.x - s1.x)
                iy = s1.y + alphaP * (s2.y - s1.y)

                iS = Vertex(ix, iy, intersect=True, alpha=alphaP)
                iC = Vertex(ix, iy, intersect=True, alpha=alphaQ)
                iS.neighbour = iC
                iC.neighbour = iS

                subject.insert_vertex(iS, s1, s2)
                clip.insert_vertex(iC, c1, c2)
                any_intersection = True

    return any_intersection


# 4. Fase 2: marcado entry/exit
def phase_two(poly, other_points):
    start = poly.first
    inside = point_in_polygon(start.point(), other_points)
    status_entry = not inside

    curr = start
    first_loop = True
    while curr is not start or first_loop:
        first_loop = False
        if curr.intersect:
            curr.entry = status_entry
            status_entry = not status_entry
        curr = curr.next
        if curr is start:
            break


# 5. Fase 3: construccion de los poligonos resultado
def phase_three(subject):
    result_polygons = []

    start = subject.first_unprocessed()
    while start is not None:
        result = []
        current = start
        
        # Guardamos la dirección de avance inicial
        forward = current.entry

        while True:
            current.visited = True
            # Si el nodo tiene un vecino, su contraparte también debe marcarse visitada
            if current.neighbour:
                current.neighbour.visited = True
                
            result.append(current.point())

            # Avanzar en la dirección actual
            if forward:
                current = current.next
            else:
                current = current.prev

            # Si encontramos una intersección, saltamos de polígono
            if current.intersect:
                current.visited = True
                current = current.neighbour
                current.visited = True
                # Cambiamos la regla de dirección basada en el nuevo polígono
                forward = current.entry

            # Condición de parada: volvimos al punto de inicio
            if current is start or (current.x == start.x and current.y == start.y):
                break

        if result:
            result_polygons.append(result)
            
        start = subject.first_unprocessed()

    return result_polygons


# 6. Funcion principal: recorte (interseccion) de dos poligonos
def greiner_hormann_clip(subject_pts, clip_pts):
    subject = Polygon()
    for x, y in subject_pts:
        subject.add(x, y)

    clip = Polygon()
    for x, y in clip_pts:
        clip.add(x, y)

    has_intersection = phase_one(subject, clip)

    if not has_intersection:
        if point_in_polygon(subject_pts[0], clip_pts):
            return [subject_pts]
        elif point_in_polygon(clip_pts[0], subject_pts):
            return [clip_pts]
        else:
            return []

    phase_two(subject, clip_pts)
    phase_two(clip, subject_pts)

    return phase_three(subject)


def cerrar(p):
    return p + [p[0]] if len(p) > 1 else p


# 7. Ejemplos predefinidos
EJEMPLOS = {
    1: ("Dos cuadrados solapados",
        [(0, 0), (4, 0), (4, 4), (0, 4)],
        [(2, 2), (6, 2), (6, 6), (2, 6)]),
    2: ("Triangulo vs rectangulo",
        [(1, 1), (5, 1), (3, 5)],
        [(2, 0), (4, 0), (4, 6), (2, 6)]),
    3: ("Estrella concava vs cuadrado",
        [(3, 0), (4, 2), (6, 2), (4.5, 3.5), (5, 6), (3, 4.5),
         (1, 6), (1.5, 3.5), (0, 2), (2, 2)],
        [(0, 1), (6, 1), (6, 5), (0, 5)]),
    4: ("Poligono contenido (sin cruces de arista)",
        [(1, 1), (2, 1), (2, 2), (1, 2)],
        [(0, 0), (5, 0), (5, 5), (0, 5)]),
}


# 8. Ventana principal
class DemoGreinerHormann:
    def __init__(self):
        self.subject_pts = []
        self.clip_pts = []
        self.modo = None        # None, 'subject' o 'clip'
        self.resultado = []

        self.fig = plt.figure(figsize=(11, 7))
        try:
            self.fig.canvas.manager.set_window_title("Demo Greiner-Hormann")
        except Exception:
            pass

        # Lienzo principal donde se dibuja todo
        self.ax = self.fig.add_axes([0.06, 0.08, 0.58, 0.82])
        self.ax.set_xlim(-1, 10)
        self.ax.set_ylim(-1, 10)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.5)

        # Texto de estado (instrucciones / resultados), arriba de todo
        self.status = self.fig.text(0.06, 0.95, "", fontsize=10.5,
                                     weight='bold', color='navy', wrap=True)

        self._crear_botones()
        self._set_status("Elige un ejemplo o presiona 'Dibujar Sujeto' para empezar.")

        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    # Construccion de la interfaz 
    def _crear_botones(self):
        left = 0.68
        width = 0.27
        height = 0.07
        gap = 0.018
        etiquetas = [
            "Ejemplo 1: Cuadrados",
            "Ejemplo 2: Triangulo",
            "Ejemplo 3: Estrella",
            "Ejemplo 4: Contenido",
            "Dibujar Sujeto",
            "Dibujar Recorte",
            "Calcular Recorte",
            "Limpiar Todo",
        ]
        self.botones = []
        top = 0.86
        for i, etiqueta in enumerate(etiquetas):
            ax_btn = self.fig.add_axes(
                [left, top - i * (height + gap), width, height])
            btn = Button(ax_btn, etiqueta)
            self.botones.append(btn)

        self.botones[0].on_clicked(lambda e: self._cargar_ejemplo(1))
        self.botones[1].on_clicked(lambda e: self._cargar_ejemplo(2))
        self.botones[2].on_clicked(lambda e: self._cargar_ejemplo(3))
        self.botones[3].on_clicked(lambda e: self._cargar_ejemplo(4))
        self.botones[4].on_clicked(self._activar_modo_sujeto)
        self.botones[5].on_clicked(self._activar_modo_recorte)
        self.botones[6].on_clicked(self._calcular)
        self.botones[7].on_clicked(self._limpiar)

    def _set_status(self, msg):
        self.status.set_text(msg)
        self.fig.canvas.draw_idle()

    #  Acciones de los botones 
    def _cargar_ejemplo(self, num):
        nombre, s, c = EJEMPLOS[num]
        self.subject_pts = list(s)
        self.clip_pts = list(c)
        self.modo = None
        self._calcular(None, titulo=nombre)

    def _activar_modo_sujeto(self, event):
        self.modo = 'subject'
        self.subject_pts = []
        self.resultado = []
        self._set_status(
            "Modo DIBUJAR SUJETO (azul): clic izquierdo = agregar punto, "
            "clic derecho = borrar el ultimo.")
        self._redibujar()

    def _activar_modo_recorte(self, event):
        self.modo = 'clip'
        self.clip_pts = []
        self.resultado = []
        self._set_status(
            "Modo DIBUJAR RECORTE (rojo): clic izquierdo = agregar punto, "
            "clic derecho = borrar el ultimo.")
        self._redibujar()

    def _calcular(self, event, titulo=None):
        self.modo = None
        if len(self.subject_pts) < 3 or len(self.clip_pts) < 3:
            self._set_status(
                "Faltan vertices: necesitas al menos 3 puntos en cada poligono "
                "(sujeto y recorte) antes de calcular.")
            self._redibujar()
            return

        self.resultado = greiner_hormann_clip(self.subject_pts, self.clip_pts)
        titulo = titulo or "Resultado del recorte"
        if self.resultado:
            self._set_status(f"{titulo}: se genero {len(self.resultado)} "
                              f"poligono(s) resultado (área verde).")
        else:
            self._set_status(f"{titulo}: sin interseccion, los poligonos no se solapan.")
        self._redibujar()

    def _limpiar(self, event):
        self.subject_pts = []
        self.clip_pts = []
        self.resultado = []
        self.modo = None
        self._set_status("Lienzo limpio. Elige un ejemplo o presiona 'Dibujar Sujeto'.")
        self._redibujar()

    #  Clics sobre el lienzo 
    def _on_click(self, event):
        if event.inaxes != self.ax or self.modo is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        punto = (round(event.xdata, 2), round(event.ydata, 2))
        lista = self.subject_pts if self.modo == 'subject' else self.clip_pts

        if event.button == 1:        # clic izquierdo -> agregar
            lista.append(punto)
        elif event.button == 3:      # clic derecho -> borrar el ultimo
            if lista:
                lista.pop()

        self._redibujar()

    #  Redibujado del lienzo 
    def _redibujar(self):
        self.ax.clear()
        self.ax.set_xlim(-1, 10)
        self.ax.set_ylim(-1, 10)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle=':', alpha=0.5)

        if self.subject_pts:
            pts = cerrar(self.subject_pts)
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.ax.plot(xs, ys, marker='o', linestyle='--',
                         color='blue', label='Sujeto (S)')

        if self.clip_pts:
            pts = cerrar(self.clip_pts)
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            self.ax.plot(xs, ys, marker='o', linestyle='--',
                         color='red', label='Recorte (C)')

        for poly in self.resultado:
            pr = cerrar(poly)
            xs, ys = [p[0] for p in pr], [p[1] for p in pr]
            self.ax.fill(xs, ys, alpha=0.4, color='green')

        if self.subject_pts or self.clip_pts or self.resultado:
            self.ax.legend(loc='upper right')

        self.fig.canvas.draw_idle()

    def mostrar(self):
        plt.show()


if __name__ == "__main__":
    demo = DemoGreinerHormann()
    demo.mostrar()