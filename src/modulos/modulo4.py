# Módulo 4 - Rasterização de polígonos
#
# Teste isolado (a partir de src/):
#     python3 modulos/modulo4.py ../data/dados_modelos2D/tree2D_Nterm032.vtk
#
# IDEIA DO MÓDULO
#   A árvore CCO é formada por segmentos (linhas) com um raio. Cada segmento vira um
#   poligono: um retângulo de largura proporcional ao raio do vaso (4 vértices).
#   Cada polígono é projetado para coordenadas de PIXEL e preenchido com o algoritmo
#   Scanline (Edge Table + Active Edge Table + regra Par-Ímpar) dentro de um buffer de
#   pixels (uma matriz N x N x 3). A cor do polígono depende do raio.
#
# Etapas:
#   segmento (P1, P2, raio) -> retângulo (4 vértices) -> pixels -> Scanline -> imagem

from pathlib import Path
import sys

import numpy as np
import pyvista as pv

import matplotlib
matplotlib.use("Agg")                           
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent))
from modulos.var_global import PATH_FILE_MOD4


TAMANHO_IMAGEM = 400        # o buffer de pixels tem 400 x 400
LARGURA_MAX_VASO = 0.035    
MEIA_LARGURA_MIN = 1.0      
COR_FUNDO = (255, 255, 255) # branco
TOLERANCIA = 1e-9           # evita erro de arredondamento de float

POSICAO_Y_BOTAO = 30                       # altura (em pixels da janela) do botão


#algoritmo Scanline 
class Aresta:
    # uma aresta nao horizontal do polígono (um 'no' da ET / AET)

    def __init__(self, y_max, x_atual, inclinacao_inversa):
        self.y_max = y_max                                   # linha onde a aresta deixa de existir
        self.x_atual = float(x_atual)                        # x onde a aresta cruza a linha atual
        self.inclinacao_inversa = float(inclinacao_inversa)  # 1/m = dx/dy

    def __repr__(self):
        return f"Aresta(ymax={self.y_max}, x={self.x_atual:.2f}, 1/m={self.inclinacao_inversa:.2f})"


def construir_tabela_de_arestas(vertices):
    # Edge Table (ET): dicionário  y_min -> lista de arestas que COMEÇAM nessa linha.
    # Arestas horizontais são descartadas (não mudam a paridade).
    tabela = {}
    quantidade = len(vertices)

    for i in range(quantidade):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % quantidade]       # o % fecha o polígono (último -> primeiro)

        if y1 == y2:                                  # aresta horizontal: ignora
            continue

        # descobre qual ponta é a de baixo (y_min) e qual é a de cima (y_max)
        if y1 < y2:
            y_min = y1
            y_max = y2
            x_no_y_min = x1
        else:
            y_min = y2
            y_max = y1
            x_no_y_min = x2

        inclinacao_inversa = (x2 - x1) / (y2 - y1)    # quanto x muda a cada +1 em y

        aresta = Aresta(y_max, x_no_y_min, inclinacao_inversa)
        if y_min not in tabela:
            tabela[y_min] = []                        # cria o "balde" desta linha
        tabela[y_min].append(aresta)

    # dentro de cada balde: menor x primeiro; se empatar, menor inclinação inversa
    for y_min in tabela:
        tabela[y_min].sort(key=lambda a: (a.x_atual, a.inclinacao_inversa))
    return tabela


def scanline_preencher(vertices, imagem, cor, mostrar_passos=False):
    
    # Para cada linha de varredura y:
    #  1. remove da AET as arestas que já terminaram (y >= y_max)
    #  2. move da ET para a AET as arestas que começam em y
    #  3. ordena a AET pelo x atual
    #  4. pinta os pixels entre pares de interseções (regra Par-Ímpar)
    #  5. atualiza x += 1/m para a próxima linha
    altura = imagem.shape[0]
    largura = imagem.shape[1]

    # y precisa ser inteiro (é índice de linha); x pode continuar fracionário
    vertices_inteiros = []
    for x, y in vertices:
        vertices_inteiros.append((x, int(round(y))))
    vertices = vertices_inteiros

    tabela = construir_tabela_de_arestas(vertices)
    if not tabela:                                    # polígono sem arestas não horizontais
        return 0

    y_inicial = min(tabela.keys())
    todos_y_max = []
    for lista_de_arestas in tabela.values():
        for aresta in lista_de_arestas:
            todos_y_max.append(aresta.y_max)
    y_final = max(todos_y_max)

    arestas_ativas = []                               # AET
    pixels_pintados = 0

    for y in range(y_inicial, y_final + 1):
        # 1) remove arestas expiradas
        arestas_filtradas = []
        for aresta in arestas_ativas:
            if y < aresta.y_max:
                arestas_filtradas.append(aresta)
        arestas_ativas = arestas_filtradas

        # 2) entram as arestas que começam nesta linha
        if y in tabela:
            arestas_ativas.extend(tabela[y])

        # 3) ordena da esquerda para a direita
        arestas_ativas.sort(key=lambda a: (a.x_atual, a.inclinacao_inversa))

        # 4) Par-Ímpar: 1ª e 2ª interseção formam um trecho, 3ª e 4ª outro etc
        trechos = []
        for i in range(0, len(arestas_ativas) - 1, 2):
            x_esquerda = arestas_ativas[i].x_atual
            x_direita = arestas_ativas[i + 1].x_atual
            coluna_inicial = int(np.ceil(x_esquerda - TOLERANCIA))    # 1º pixel inteiro >= x_esquerda
            coluna_final = int(np.floor(x_direita + TOLERANCIA))      # último pixel inteiro <= x_direita
            trechos.append((coluna_inicial, coluna_final))

            if 0 <= y < altura:                       # só pinta dentro do buffer
                c0 = max(0, coluna_inicial)
                c1 = min(largura - 1, coluna_final)
                if c0 <= c1:
                    imagem[y, c0:c1 + 1] = cor        # pinta o trecho inteiro de uma vez
                    pixels_pintados += c1 - c0 + 1

        if mostrar_passos:
            print(f"y={y:2d}  AET={[(round(a.x_atual, 2), a.y_max) for a in arestas_ativas]}"
                  f"  trechos={trechos}")

        # 5) próxima linha: x de cada aresta anda 1/m
        for aresta in arestas_ativas:
            aresta.x_atual += aresta.inclinacao_inversa

    return pixels_pintados


# Parte 2: árvore -> polígonos -> pixels
def obter_raios(malha, estado):
    # raio de cada célula (= segmento). Oo módulo 1 já calculou
    if estado is not None and "raios" in estado:
        return np.asarray(estado["raios"], dtype=float)
    for nome in malha.cell_data.keys():
        if "raio" in nome.lower() or "radius" in nome.lower():
            return np.asarray(malha.cell_data[nome], dtype=float)
    raise KeyError("Atributo de raio não encontrado na malha.")


def obter_segmentos(malha, raios):
    # Lista de segmentos: (x1, y1, z1, x2, y2, z2, raio)
    pontos = np.asarray(malha.points)
    segmentos = []
    for i in range(malha.n_cells):
        ids = list(malha.get_cell(i).point_ids)
        for j in range(len(ids) - 1):
            a = pontos[ids[j]]
            b = pontos[ids[j + 1]]
            segmentos.append((float(a[0]), float(a[1]), float(a[2]),
                              float(b[0]), float(b[1]), float(b[2]), float(raios[i])))
    return segmentos


def rotacionar(x, y, z, centro, angulo_graus, modelo_2d):
    # Gira o ponto em torno do centro do modelo. 3D: eixo Y. 2D: eixo Z (no próprio plano).
    angulo = np.radians(angulo_graus)
    c = np.cos(angulo)
    s = np.sin(angulo)
    dx = x - centro[0]
    dy = y - centro[1]
    dz = z - centro[2]
    if modelo_2d:
        return centro[0] + dx * c - dy * s, centro[1] + dx * s + dy * c, z
    return centro[0] + dx * c + dz * s, y, centro[2] - dx * s + dz * c


def criar_poligono_do_vaso(x1, y1, x2, y2, meia_largura):
    # Transforma o segmento P1->P2 em um retângulo de 4 vértices (em pixels).
    #   d = direção do segmento (vetor unitário)
    #   n = normal (perpendicular) a d
    #   vértices = P1 +- n*h  e  P2 +- n*h   (h = meia largura)
    # As pontas são estendidas em h ("tampa quadrada") para as junções entre vasos não
    # deixarem buracos.
    dx = x2 - x1
    dy = y2 - y1
    comprimento = np.sqrt(dx * dx + dy * dy)
    if comprimento == 0:
        return None                                   # segmento de tamanho zero: sem polígono
    dir_x = dx / comprimento
    dir_y = dy / comprimento
    normal_x = -dir_y
    normal_y = dir_x

    ini_x = x1 - dir_x * meia_largura                 # estende a ponta inicial
    ini_y = y1 - dir_y * meia_largura
    fim_x = x2 + dir_x * meia_largura                 # estende a ponta final
    fim_y = y2 + dir_y * meia_largura

    return [(ini_x + normal_x * meia_largura, ini_y + normal_y * meia_largura),
            (fim_x + normal_x * meia_largura, fim_y + normal_y * meia_largura),
            (fim_x - normal_x * meia_largura, fim_y - normal_y * meia_largura),
            (ini_x - normal_x * meia_largura, ini_y - normal_y * meia_largura)]


def cor_do_raio(raio, raio_min, raio_max):
    # Mesma regra de cor do módulo 1:  t = (r - rmin)/(rmax - rmin);  R = t, G = 0.5, B = 1 - t
    if raio_max == raio_min:
        t = 0.0
    else:
        t = (raio - raio_min) / (raio_max - raio_min)
    return (int(255 * t), 128, int(255 * (1.0 - t)))


def rasterizar_arvore(segmentos, config, angulo_graus=0.0):
    n = config["tamanho"]
    imagem = np.zeros((n, n, 3), dtype=np.uint8)
    imagem[:, :] = COR_FUNDO

    centro = config["centro"]
    pixels_por_unidade = config["pixels_por_unidade"]
    raio_min = config["raio_min"]
    raio_max = config["raio_max"]
    meia_largura_max = LARGURA_MAX_VASO * n / 2

    vasos = []
    for x1, y1, z1, x2, y2, z2, raio in segmentos:
        rx1, ry1, rz1 = rotacionar(x1, y1, z1, centro, angulo_graus, config["modelo_2d"])
        rx2, ry2, rz2 = rotacionar(x2, y2, z2, centro, angulo_graus, config["modelo_2d"])
        # mundo -> pixel: centro do modelo vai para o meio da imagem
        px1 = (rx1 - centro[0]) * pixels_por_unidade + n / 2
        py1 = (ry1 - centro[1]) * pixels_por_unidade + n / 2
        px2 = (rx2 - centro[0]) * pixels_por_unidade + n / 2
        py2 = (ry2 - centro[1]) * pixels_por_unidade + n / 2
        meia_largura = max(MEIA_LARGURA_MIN, meia_largura_max * raio / raio_max)
        profundidade = (rz1 + rz2) / 2
        vasos.append((profundidade, raio, px1, py1, px2, py2, meia_largura))

    vasos.sort(key=lambda v: (v[0], -v[1]))

    #cada vaso vira polígono e é preenchido pelo Scanline
    total_poligonos = 0
    total_pixels = 0
    for profundidade, raio, px1, py1, px2, py2, meia_largura in vasos:
        poligono = criar_poligono_do_vaso(px1, py1, px2, py2, meia_largura)
        if poligono is None:
            continue
        cor = cor_do_raio(raio, raio_min, raio_max)
        total_pixels += scanline_preencher(poligono, imagem, cor)
        total_poligonos += 1

    return imagem, total_poligonos, total_pixels


def montar_configuracao(malha, raios):
    x_min, x_max, y_min, y_max, z_min, z_max = malha.bounds
    centro = ((x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2)
    modelo_2d = (z_max - z_min) < 1e-9 * max(malha.length, 1e-12)
    # raio da esfera que envolve o modelo: a imagem é quadrada e cabe o modelo em QUALQUER rotação
    raio_esfera = 0.5 * malha.length
    lado_do_mundo = 2 * raio_esfera * 1.05
    return {"tamanho": TAMANHO_IMAGEM, "centro": centro, "modelo_2d": modelo_2d,
            "lado_do_mundo": lado_do_mundo,
            "pixels_por_unidade": TAMANHO_IMAGEM / lado_do_mundo,
            "raio_min": float(np.min(raios)), "raio_max": float(np.max(raios)),
            "limites": (x_min, x_max, y_min, y_max, z_min, z_max)}


def criar_malha_de_pixels(imagem, config):
    n = config["tamanho"]
    lado = config["lado_do_mundo"]
    x_min, x_max, y_min, y_max, z_min, z_max = config["limites"]
    tam_pixel = lado / n
    origem_x = x_max + 0.15 * (x_max - x_min)                  # q direita da árvore
    origem_y = (y_min + y_max) / 2 - lado / 2                  # centralizada na vertical
    origem = (origem_x, origem_y, config["centro"][2])
    dimensoes = (n + 1, n + 1, 1)                              # n células = n+1 pontos
    espacamento = (tam_pixel, tam_pixel, 1.0)
    try:
        malha = pv.ImageData(dimensions=dimensoes, spacing=espacamento, origin=origem)
    except AttributeError:                                  
        malha = pv.UniformGrid(dims=dimensoes, spacing=espacamento, origin=origem)

    malha.cell_data["cor"] = imagem.reshape(-1, 3)
    return malha


def desenhar_imagem(plotter, estado4):
    imagem, poligonos, pixels = rasterizar_arvore(estado4["segmentos"], estado4["config"],
                                                  estado4["angulo"])
    estado4["imagem"] = imagem
    malha = criar_malha_de_pixels(imagem, estado4["config"])

    try:
        plotter.remove_actor("m4_imagem")                      # tira a imagem anterior
    except Exception:
        pass
    ator = plotter.add_mesh(malha, scalars="cor", rgb=True, preference="cell",
                            lighting=False, show_scalar_bar=False,
                            name="m4_imagem", reset_camera=False)
    ator.SetVisibility(estado4["visivel"])                    
    estado4["ator"] = ator

    total = estado4["config"]["tamanho"] ** 2
    plotter.add_text(f"Scanline: {poligonos} polígonos (vasos) | {pixels} pixels pintados "
                     f"({100 * pixels / total:.1f}% do buffer, com sobreposição)",
                     position="upper_right", font_size=9, name="info_modulo4")
    plotter.render()
    return poligonos, pixels


def rasterizacao_poligono(plotter: pv.Plotter, estado: dict = None) -> dict:
    if estado is None or "mesh" not in estado:
        print("[Módulo 4] precisa do 'estado' do módulo 1:  rasterizacao_poligono(plotter, estado)")
        return None

    malha = estado["mesh"]
    raios = obter_raios(malha, estado)
    segmentos = obter_segmentos(malha, raios)
    config = montar_configuracao(malha, raios)

    estado4 = {"segmentos": segmentos, "config": config, "angulo": 0.0,
               "visivel": True, "imagem": None, "ator": None}

    poligonos, pixels = desenhar_imagem(plotter, estado4)
    print(f"[Módulo 4] {len(segmentos)} segmentos -> {poligonos} polígonos (retângulos de 4 vértices)")
    print(f"[Módulo 4] Pixels pintados pelo Scanline: {pixels} (buffer {config['tamanho']}x{config['tamanho']})")

    # salva o PNG 
    pasta_figuras = Path(__file__).resolve().parents[2] / "report" / "figures"
    salvar_png(estado4["imagem"], pasta_figuras / "modulo4_arvore_scanline.png")

    #botão: mostrar/esconder a imagem
    def ao_clicar(ligado):
        estado4["visivel"] = bool(ligado)
        estado4["ator"].SetVisibility(bool(ligado))        
        plotter.render()

    plotter.add_checkbox_button_widget(ao_clicar, value=True, position=(10, POSICAO_Y_BOTAO),
                                       size=32, color_on="green", color_off="grey")
    plotter.add_text("Árvore rasterizada (Scanline)", position=(52, POSICAO_Y_BOTAO + 6),
                     font_size=10, name="rot_modulo4")

    return estado4


# função para salvar a figura
def salvar_png(imagem, caminho):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(str(caminho), np.flipud(imagem))              
    print(f"[Módulo 4] Figura salva em: {caminho}")





if __name__ == "__main__":

    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = PATH_FILE_MOD4

    malha = pv.read(caminho)
    p = pv.Plotter()
    p.add_mesh(malha, color="firebrick", line_width=2)   
    rasterizacao_poligono(p, {"mesh": malha})
    p.view_xy()
    p.show()