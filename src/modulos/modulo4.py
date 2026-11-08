# Módulo 4 - Rasterização de polígonos (aula 10): preenchimento Scanline.
#
# Uso pela main:
#     rasterizacao_poligono(plotter, estado)      # 'estado' é o dict devolvido pelo módulo 1
#                                                 # (opcional: sem ele usa plotter.bounds)
#
# Teste isolado (a partir de src/):
#     python3 modulos/modulo4.py ../data/dados_modelos2D/tree2D_Nterm008.vtk
#
# O que faz:
#  1. Define um polígono CÔNCAVO (a "região de interesse") sobre o domínio da árvore.
#  2. Rasteriza esse polígono com o algoritmo Scanline (Edge Table + Active Edge Table
#     + regra Par-Ímpar), implementado por nós SEM usar nenhuma função pronta da biblioteca.
#  3. Mostra na cena a grade de pixels, os pixels preenchidos e o contorno do polígono.
#  4. Conta pixels preenchidos (fill-rate) e quantos vértices da árvore caem dentro da região.
#  5. Um botão liga/desliga a visualização.
#
# Quem fez o quê:
#   Nosso código  : Aresta, tabela de arestas (ET), laço Scanline (AET), regra Par-Ímpar.
#   Biblioteca    : PyVista só DESENHA (grade, pixels, linhas, botão).

from pathlib import Path
import sys

import numpy as np
import pyvista as pv

import matplotlib
matplotlib.use("Agg")                           # não abre janela, só gera o arquivo
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
LARGURA_GRADE = 30     # nº de pixels na horizontal da grade
ALTURA_GRADE = 26      # nº de pixels na vertical da grade

# Polígono côncavo de teste (mesmo do código do professor), em coordenadas de PIXEL.
POLIGONO_EXEMPLO = [(3, 3), (12, 5), (22, 2), (17, 12),
                    (26, 21), (14, 18), (7, 23), (9, 13)]

POSICAO_Y_BOTAO = 30  # altura (em pixels da janela) do botão
TOLERANCIA = 1e-9      # evita erro de arredondamento de float 


# Parte 1: algoritmo Scanline (matemática pura, sem PyVista)
class Aresta:
    #Uma aresta NÃO horizontal do polígono (um 'nó' da ET / AET)

    def __init__(self, y_max, x_atual, inclinacao_inversa):
        self.y_max = y_max                          # onde a aresta deixa de existir
        self.x_atual = float(x_atual)               # x coordenada inicial da aresta no ponto inferior (y_min)
        self.inclinacao_inversa = float(inclinacao_inversa)  # 1/m, ou seja é a inclinação inversa da reta(aresta)

    #Imprimir na tela 
    def __repr__(self):
        return f"Aresta(ymax={self.y_max}, x={self.x_atual:.2f}, 1/m={self.inclinacao_inversa:.2f})"


# função q organiza as arestas do poligono na tabela
def construir_tabela_de_arestas(vertices):
    #"""Edge Table (ET): dicionário  y_min -> lista de arestas que COMEÇAM nessa linha.
    #Arestas horizontais são descartadas (não mudam a paridade)."""
    tabela = {}
    quantidade = len(vertices) #quantidade de pontos

    for i in range(quantidade):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % quantidade]     # o % fecha o polígono (quando o i = quantidade x2 e y2 é igual a primeiro)

        if y1 == y2:                                # aresta horizontal: ignora
            continue

        # descobre qual ponta é a de baixo (y_min) e qual é a de cima (y_max)
        if y1 < y2:
            y_max = y2
            y_min = y1
            x_no_y_min = x1
        else:
            y_max = y1
            y_min = y2
            x_no_y_min = x2

        if (x2 - x1) == 0:
            inclinacao = 0
        else:
            inclinacao = (y2-y1) / (x2-x1)

        if inclinacao == 0:
            inclinacao_inversa = 0
        else: 
            inclinacao_inversa = 1.0 / inclinacao  
        #cria a aresta
        aresta = Aresta(y_max, x_no_y_min, inclinacao_inversa)

        if y_min not in tabela:
            tabela[y_min] = []  #se  y_min não tiver na tabela ainda cria um balde para cada
        
        tabela[y_min].append(aresta)

    # dentro de cada balde ordena as arestas do menor x para o maior, se empatar ordena pela menor inclinação inversa (a q mais inclina para esquerda)
    for y_min in tabela:
        tabela[y_min].sort(key=lambda a: (a.x_atual, a.inclinacao_inversa))
    return tabela


def scanline_preencher(vertices, largura, altura, mostrar_passos=False):
    #Preenche o polígono. Retorna uma matriz, se o valor for 1 ( vertice dentro) se for 0 (vertice fora).
    #Para cada linha de varredura y:
    #  1. remove da AET (tabela q armazena arestas que estão dentro) as arestas que já terminaram (y >= y_max)
    #  2. move da ET para a AET as arestas que começam em y_min = y
    #  3. ordena a AET pelo x atual
    #  4. preenche os pixels entre pares de interseções (regra Par-Ímpar)
    #  5. atualiza x += 1/m para a próxima linha

    # y precisa ser inteiro (é índice de linha) ja x pode continuar igual
    vertices_temp = []
    for x, y in vertices:
        vertices_temp.append((x, int(round(y)))) #arredonda o y para ser inteiro
    vertices = vertices_temp

    grade = np.zeros((altura, largura), dtype=int)
    tabela = construir_tabela_de_arestas(vertices)

    if not tabela:                                  # polígono sem arestas não horizontais
        return grade #retorna grade de zeros mesmo, se não existir a tabela

    #y inicial
    y_inicial = min(tabela.keys())

    #encontrar o y_final
    todos_y_max = []
    for arestas in tabela.values():
        for a in arestas:
            todos_y_max.append(a.y_max)
    y_final = max(todos_y_max)

    arestas_ativas = []                             # AET (tabela arestas ativas)

    #loop do y_inicial ate y_fiinal
    for y in range(y_inicial, y_final + 1):
        # 1)remove arestas expiradas
        arestas_filtradas = []
        for a in arestas_ativas:
            if y < a.y_max:
                arestas_filtradas.append(a)
        arestas_ativas = arestas_filtradas

        # 2)entram as arestas que começam nesta linha
        if y in tabela:
            arestas_ativas.extend(tabela[y])

        # 3)ordena da esquerda para a direita
        arestas_ativas.sort(key=lambda a: (a.x_atual, a.inclinacao_inversa))

        # 4) Par-Ímpar: 1ª e 2ª interseção formam um trecho, 3ª e 4ª outro, ...
        trechos = []
        #começa do indice 0 e opula de 2 em 2 ate percorrer todas as arestas
        for i in range(0, len(arestas_ativas) - 1, 2):
            x_esquerda = arestas_ativas[i].x_atual
            x_direita = arestas_ativas[i + 1].x_atual
            # primeiro pixel inteiro >= x_esquerda e último <= x_direita
            coluna_inicial = int(np.ceil(x_esquerda - TOLERANCIA)) # arredonda para cima
            coluna_final = int(np.floor(x_direita + TOLERANCIA)) #arredonda para baiixo
            trechos.append((coluna_inicial, coluna_final))

            if 0 <= y < altura:                     # só desenha dentro da grade
                c0 = max(0, coluna_inicial)
                c1 = min(largura - 1, coluna_final)
                if c0 <= c1:
                    grade[y, c0:c1 + 1] = 1

        if mostrar_passos:
            print(f"y={y:2d}  AET={[(round(a.x_atual, 2), a.y_max) for a in arestas_ativas]}"
                  f"  trechos={trechos}")

        # 5)proxima linha: x de cada aresta anda 1/m
        for aresta in arestas_ativas:
            aresta.x_atual += aresta.inclinacao_inversa

    return grade


# Criar imagem
def criar_imagem_de_pixels(largura, altura, x_min, y_min, tam_pixel_x, tam_pixel_y, z):
    dimensoes = (largura + 1, altura + 1, 1)
    espacamento = (tam_pixel_x, tam_pixel_y, 1.0)
    origem = (x_min, y_min, z)
    try:
        return pv.ImageData(dimensions=dimensoes, spacing=espacamento, origin=origem)
    except AttributeError:                          # pyvista < 0.40
        return pv.UniformGrid(dims=dimensoes, spacing=espacamento, origin=origem)


def rasterizacao_poligono(plotter: pv.Plotter, estado: dict = None) -> dict:
    
    if estado is not None and "mesh" in estado:
        malha_arvore = estado["mesh"]
        x_min, x_max, y_min, y_max, z_min, z_max = malha_arvore.bounds  #valores com minmos e maximos das coordenadas
        pontos_arvore = np.asarray(malha_arvore.points)
        diagonal = malha_arvore.length
    else:                                           # sem o estado do módulo 1
        x_min, x_max, y_min, y_max, z_min, z_max = plotter.bounds  #valores com minmos e maximos das coordenadas
        pontos_arvore = None
        diagonal = float(np.linalg.norm([x_max - x_min, y_max - y_min, z_max - z_min]))

    #rasteriza o polígono na grade de pixels
    grade = scanline_preencher(POLIGONO_EXEMPLO, LARGURA_GRADE, ALTURA_GRADE)
    total_pixels = LARGURA_GRADE * ALTURA_GRADE
    pixels_preenchidos = int(grade.sum()) #soma de todos elementos da grade
    taxa_de_preenchimento = pixels_preenchidos / total_pixels
    print(f"[Módulo 4] Pixels preenchidos: {pixels_preenchidos} de {total_pixels} "
          f"({100 * taxa_de_preenchimento:.1f}%)")


    #tamanho físico real de cada pixel
    tam_pixel_x = (x_max - x_min) / LARGURA_GRADE
    tam_pixel_y = (y_max - y_min) / ALTURA_GRADE
    z_plano = z_min - 0.002 * diagonal              # plano um pouco atrás da árvore

    #malha de pixels com o resultado 
    imagem = criar_imagem_de_pixels(LARGURA_GRADE, ALTURA_GRADE, x_min, y_min,
                                    tam_pixel_x, tam_pixel_y, z_plano)
    # flatten(): linha por linha, o que coincide com a ordem das células da malha (x varia mais rápido)
    imagem.cell_data["preenchido"] = grade.flatten().astype(float)

    # threshold: pega só as células cujo valor >= 0.5, ou seja, os pixels preenchidos
    so_preenchidos = imagem.threshold(0.5, scalars="preenchido")

    # contorno do polígono em coordenadas do mundo (o 1º ponto é repetido para fechar)
    # a coordenada de pixel (px, py) vira  x_min + (px + 0.5) * tam_pixel
    contorno_mundo = [[x_min + (px + 0.5) * tam_pixel_x,
                       y_min + (py + 0.5) * tam_pixel_y,
                       z_plano] for px, py in POLIGONO_EXEMPLO]
    contorno_mundo.append(contorno_mundo[0])
    contorno = pv.PolyData(np.array(contorno_mundo))
    quantidade = len(contorno_mundo)
    contorno.lines = np.hstack([[quantidade], np.arange(quantidade)])  #conectividade das linhas

    #vértices da árvore dentro da região
    dentro = np.zeros(0, dtype=bool) #array vazio,  para saber se o elemento ta preenchido
    pontos_dentro = np.zeros((0, 3)) #matriz para armaenar as coordenadas, vazio
    if pontos_arvore is not None:
        lista_x = ((pontos_arvore[:, 0] - x_min) / tam_pixel_x).astype(int)
        lista_y = ((pontos_arvore[:, 1] - y_min) / tam_pixel_y).astype(int)
        #restringir aos limites
        colunas = np.clip(lista_x, 0, LARGURA_GRADE - 1)
        linhas = np.clip(lista_y, 0, ALTURA_GRADE - 1)
        dentro = grade[linhas, colunas] == 1        # True se o pixel daquele ponto está preenchido
        pontos_dentro = pontos_arvore[dentro]    #filtra paras os pontos q estão dentro
        print(f"[Módulo 4] Vértices da árvore dentro da região: {int(dentro.sum())} de {len(pontos_arvore)}")

    #desenha
    atores = []                                     # guardados para o botão ligar/desligar
    atores.append(plotter.add_mesh(imagem, style="wireframe", color="gray", opacity=0.3,
                                   name="m4_grade"))
    if so_preenchidos.n_cells > 0:
        atores.append(plotter.add_mesh(so_preenchidos, color="deepskyblue", opacity=0.6,
                                       show_edges=True, edge_color="white", name="m4_pixels"))
    atores.append(plotter.add_mesh(contorno, color="red", line_width=3, name="m4_contorno"))
    if len(pontos_dentro) > 0:
        atores.append(plotter.add_points(pontos_dentro, color="yellow", point_size=10,
                                         render_points_as_spheres=True, name="m4_pontos"))

    plotter.add_text(f"Scanline: {pixels_preenchidos}/{total_pixels} pixels ({100 * taxa_de_preenchimento:.1f}%)\n"
                     f"vértices na região: {int(dentro.sum())}",
                     position="upper_right", font_size=9, name="info_modulo4")

    #botão para mostrar/esconder
    def ao_clicar(ligado):
        for ator in atores:
            ator.SetVisibility(bool(ligado))        # método do VTK: mostra/esconde o objeto
        plotter.render()

    plotter.add_checkbox_button_widget(ao_clicar, value=True, position=(10, POSICAO_Y_BOTAO),
                                       size=32, color_on="green", color_off="grey")
    plotter.add_text("Polígono rasterizado (Scanline)", position=(52, POSICAO_Y_BOTAO + 6),
                     font_size=10, name="rot_modulo4")

    return {"grade": grade, "pixels_preenchidos": pixels_preenchidos,
            "taxa_de_preenchimento": taxa_de_preenchimento, "pontos_dentro": pontos_dentro}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = "../../data/dados_modelos2D/tree2D_Nterm008.vtk"

    malha = pv.read(caminho)
    p = pv.Plotter()
    p.add_mesh(malha, color="firebrick", line_width=2)   # só para dar contexto no teste isolado
    rasterizacao_poligono(p, {"mesh": malha})
    p.view_xy()
    p.show()