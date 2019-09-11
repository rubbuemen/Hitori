import collections
import heapq
import types


class ListaNodos(collections.deque):
    def añadir(self, nodo):
        self.append(nodo)

    def vaciar(self):
        self.clear()

    def __contains__(self, nodo):
        return any(x.estado == nodo.estado
                   for x in self)


class PilaNodos(ListaNodos):
    def sacar(self):
        return self.pop()


class ColaNodos(ListaNodos):
    def sacar(self):
        return self.popleft()


class ColaNodosConPrioridad:
    def __init__(self):
        self.nodos = []
        self.nodo_generado = 0

    def añadir(self, nodo):
        heapq.heappush(self.nodos, (nodo.heurística, self.nodo_generado, nodo))
        self.nodo_generado += 1

    def sacar(self):
        return heapq.heappop(self.nodos)[2]

    def vaciar(self):
        self.__init__()

    def __iter__(self):
        return iter(self.nodos)

    def __contains__(self, nodo):
        return any(x[2].estado == nodo.estado and
                   x[2].heurística <= nodo.heurística
                   for x in self.nodos)


class NodoSimple:
    def __init__(self, estado, padre=None, acción=None):
        self.estado = estado
        self.padre = padre
        self.acción = acción

    def es_raíz(self):
        return self.padre is None

    def sucesor(self, acción):
        Nodo = self.__class__
        return Nodo(acción.aplicar(self.estado), self, acción)

    def solución(self):
        if self.es_raíz():
            acciones = []
        else:
            acciones = self.padre.solución()
            acciones.append(self.acción.nombre)
        return acciones

    def __str__(self):
        return 'Estado: {}'.format(self.estado)


class NodoConProfundidad(NodoSimple):
    def __init__(self, estado, padre=None, acción=None):
        super().__init__(estado, padre, acción)
        if self.es_raíz():
            self.profundidad = 0
        else:
            self.profundidad = padre.profundidad + 1

    def __str__(self):
        return 'Estado: {0}; Prof: {1}'.format(self.estado, self.profundidad)


class NodoConHeurística(NodoSimple):
    def __init__(self, estado, padre=None, acción=None):
        super().__init__(estado, padre, acción)
        if self.es_raíz():
            self.profundidad = 0
            self.coste = 0
        else:
            self.profundidad = padre.profundidad + 1
            self.coste = padre.coste + acción.coste_de_aplicar(padre.estado)
        self.heurística = self.f(self)

    @staticmethod
    def f(nodo):
        return 0

    def __str__(self):
        return 'Estado: {0}; Prof: {1}; Heur: {2}; Coste: {3}'.format(
            self.estado, self.profundidad, self.heurística, self.coste)


class BúsquedaGeneral:
    def __init__(self, detallado=False):
        self.detallado = detallado
        if self.detallado:
            self.Nodo = NodoConProfundidad
        else:
            self.Nodo = NodoSimple
        self.explorados = ListaNodos()

    def es_expandible(self, nodo):
        return True

    def expandir_nodo(self, nodo, problema):
        return (nodo.sucesor(acción)
                for acción in problema.acciones_aplicables(nodo.estado))

    def es_nuevo(self, nodo):
        return (nodo not in self.frontera and
                nodo not in self.explorados)

    def buscar(self, problema):
        self.frontera.vaciar()
        self.explorados.vaciar()
        self.frontera.añadir(self.Nodo(problema.estado_inicial))
        while True:
            if not self.frontera:
                return None
            nodo = self.frontera.sacar()
            if self.detallado:
                print('{0}Nodo: {1}'.format('  ' * nodo.profundidad, nodo))
            if problema.es_estado_final(nodo.estado):
                return nodo.solución()
            self.explorados.añadir(nodo)
            if self.es_expandible(nodo):
                nodos_hijos = self.expandir_nodo(nodo, problema)
                for nodo_hijo in nodos_hijos:
                    if self.es_nuevo(nodo_hijo):
                        self.frontera.añadir(nodo_hijo)


class BúsquedaEnAnchura(BúsquedaGeneral):
    def __init__(self, detallado=False):
        super().__init__(detallado)
        self.frontera = ColaNodos()


class BúsquedaEnProfundidad(BúsquedaGeneral):
    def __init__(self, detallado=False):
        super().__init__(detallado)
        self.frontera = PilaNodos()
        self.explorados = PilaNodos()

        def añadir_vaciando_rama(self, nodo):
            if self:
                while True:
                    último_nodo = self.pop()
                    if último_nodo == nodo.padre:
                        self.append(último_nodo)
                        break
            self.append(nodo)
        self.explorados.añadir = types.MethodType(añadir_vaciando_rama,
                                                  self.explorados)


class BúsquedaEnProfundidadAcotada(BúsquedaEnProfundidad):
    def __init__(self, cota, detallado=False):
        super().__init__(detallado)
        self.Nodo = NodoConProfundidad
        self.cota = cota

    def es_expandible(self, nodo):
        return nodo.profundidad < self.cota


class BúsquedaEnProfundidadIterativa:
    def __init__(self, cota_final, cota_inicial=0, detallado=False):
        self.cota_inicial = cota_inicial
        self.cota_final = cota_final
        self.detallado = detallado

    def buscar(self, problema):
        for cota in range(self.cota_inicial, self.cota_final):
            bpa = BúsquedaEnProfundidadAcotada(cota, self.detallado)
            solución = bpa.buscar(problema)
            if solución:
                return solución


class BúsquedaPrimeroElMejor(BúsquedaGeneral):
    def __init__(self, f, detallado=False):
        super().__init__(detallado)
        self.Nodo = NodoConHeurística
        self.Nodo.f = staticmethod(f)
        self.frontera = ColaNodosConPrioridad()
        self.explorados = ListaNodos()
        self.explorados.__contains__ = types.MethodType(
            lambda self, nodo: any(x.estado == nodo.estado and
                                   x.heurística <= nodo.heurística
                                   for x in self),
            self.explorados)


class BúsquedaÓptima(BúsquedaPrimeroElMejor):
    def __init__(self, detallado=False):
        def coste(nodo):
            return nodo.coste
        super().__init__(coste, detallado)


class BúsquedaAEstrella(BúsquedaPrimeroElMejor):
    def __init__(self, h, detallado=False):
        def coste(nodo):
            return nodo.coste

        def f(nodo):
            return coste(nodo) + h(nodo)
        super().__init__(f, detallado)
