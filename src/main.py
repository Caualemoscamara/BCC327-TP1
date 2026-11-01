# Modulo 1 - Leitura, primitivas e atributos
# Modulo 2 - Transformações geométricas e observador
# Modulo 3 - Rasterização de linhas
# Modulo 4 - Rasterização de poligonos
# Modulo 5 - Aliasing e antialiasing
# Modulo 6 - Recorte de segmento de reta
# Modulo 7 - Recorte de poligonos

# Interações:
#   Alternar vistas e projeções
#   Rotação e zoom
#   Ligar/desligar antialiasing
#   Seleção do algoritmo de recorte
#   Exibiçao da janela/região de corte
#   Alternância entre mapa de cores e espessura proporcional ao raio

import pyvista as pv
import sys

from modulos.modulo1 import read_and_config
from modulos.modulo2 import view_widgets
from modulos.modulo3 import rasterizacao_linhas
from modulos.modulo4 import rasterizacao_poligono
from modulos.modulo5 import aliasing_widgets
from modulos.modulo6 import clipping_line_region
from modulos.modulo7 import clipping_polygon_region

# Ver como passar argc e argv no python
PATH_FILE = "../data/dados_modelos2D/tree2D_Nterm008.vtk"


def main(caminho):
    plotter = pv.Plotter()

    # Modulo 1 - Leitura, primitivas e atributos
    read_and_config(plotter, caminho)

    # Modulo 2 - Transformações geométricas e observador
    view_widgets(plotter)

    # Modulo 3 - Rasterização de linhas
    rasterizacao_linhas(plotter)

    # Modulo 4 - Rasterização de poligonos
    rasterizacao_poligono(plotter)

    # Modulo 5 - Aliasing e antialiasing
    aliasing_widgets(plotter)

    # Modulo 6 - Recorte de segmento de reta
    clipping_line_region(plotter)

    # Modulo 7 - Recorte de poligonos
    clipping_polygon_region(plotter)


    plotter.show()

    return 0


if __name__ == "__main__":
    #qual arquivo?
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = PATH_FILE

    main(caminho)