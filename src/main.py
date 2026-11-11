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
from modulos.modulo5 import aliasing_widgets
import modulos.var_global


def main(caminho):
    plotter = pv.Plotter(window_size=[1920, 1080])
    plotter.camera_position = 'yz'


    # Modulo 1 - Leitura, primitivas e atributos
    estado = read_and_config(plotter, caminho)

    # Modulo 2 - Transformações geométricas e observador
    view_widgets(plotter)

    # Modulo 3 - Rasterização de linhas
    rasterizacao_linhas(caminho)

    # Modulo 5 - Aliasing e antialiasing
    aliasing_widgets(plotter)


    plotter.show()

    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = modulos.var_global.PATH_FILE_DEFAULT

    main(caminho)