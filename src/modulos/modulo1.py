#Módulo 1 - Leitura, primitivas e atributos de modelos CCO (aulas 4 e 5).

#Uso pela main:
#    estado = read_and_config(plotter, caminho_vtk)

#Teste isolado:
#    python3 modulos/modulo1.py ../data/dados_modelos2D/tree2D_Nterm008.vtk
#    (rodando a partir de src/)

#O que faz:
#  1. Lê o .vtk e informa nº de pontos, nº de segmentos e raio mín/máx.
#  2. Representa cada segmento como um tubo (cilindro de 8 lados).
#  3. Dois botões independentes:
#        [Cor]       cor RGB em função do raio (azul = fino -> vermelho = grosso)
#        [Espessura] espessura do tubo proporcional ao raio
#     (ligados juntos, só um, ou nenhum).


import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from matplotlib.colors import ListedColormap

#constantes
TITULO_BARRA = "Raio do Vaso"
N_LADOS = 8


#função para obter numeros de pontos e atributos
def obeter_atributos(mesh):
    numero_pontos = mesh.n_points
    numero_segmentos = mesh.n_cells
    return numero_pontos, numero_segmentos

#Função para obter raio
def obter_raio(mesh):
    #percorre todos os atributis
    for nome in mesh.array_names:
        #se o nome em minusculo for igual a raio, radius ou radii, armazena o noime real
        if "raio" in nome.lower() or "radius" in nome.lower() or "radii" in nome.lower():
            nome_raio = nome
            break
    
    #cálcula o minimo e o maximo
    if nome_raio:
        raios = mesh.cell_data[nome_raio] #pega todos os valores numeros que são os raios
        raio_min = np.min(raios)
        raio_max = np.max(raios)

    return nome_raio, raios, raio_min, raio_max

#Função que obtem o segmento
def obter_segmentos(mesh, numero_segmentos):
    idx = [] #lista para armazenar indices 
    cel = [] #lista para associar o segmento a sua celula original

    for celula in range(numero_segmentos):
        ids_pontos_da_celula = list(mesh.get_cell(celula).point_ids) #lista de ids dos pontos q compoe o segmento

        #separar os segmentos em dois pontos
        for i in range(len(ids_pontos_da_celula) - 1):
            ponto_inicio = ids_pontos_da_celula[i] #onde o segmento comeca
            ponto_fim = ids_pontos_da_celula[i+1] #proximo ponto é o fim do segmento

            #guarda o par de indices
            idx.append((ponto_inicio, ponto_fim))
            #guarda o egmento original
            cel.append(celula)

    array_idx = np.array(idx)
    array_cel = np.array(cel)

    return array_idx, array_cel

# define o ,mapa de cores pelo RGB
def mapa_rgb(n=256):
    t = np.linspace(0.0, 1.0, n)  # Cria 'n' valores de 0 a 1 (o equivalente aos raios normalizados)
    
    vermelho = t   ## Vermelho varia de 0 a 1
    verde = np.full(n, 0.5)  #verde constante 0.5
    azul = 1.0 - t   #Azul varia de 1 a 0
    
    # Retorna o colormap pronto para o Matplotlib/PyVista
    return ListedColormap(np.column_stack([vermelho, verde, azul]))

# Função que controi os segmentos
def montar_segmentos(mesh, raios_cel, numero_segmentos):

    #obter lista de indices de par de pontos q representa segmento e a lista de segmentos original
    idx, cel = obter_segmentos(mesh, numero_segmentos)

    r = raios_cel[cel] # lista dos raios de cada segmento
    M = len(idx)   # Numero total de segmentos

    pontos_originais = np.asarray(mesh.points)

    #criar pontos para cada segmento
    pontos = []
    for par in idx:
        p1 = pontos_originais[par[0]]
        p2 = pontos_originais[par[1]]
        pontos.append(p1)
        pontos.append(p2)
    
    pontos = np.array(pontos)

    #cria as linhas, cada linha é composta por 2 pontos
    linhas = []
    for i in range(M):
        linhas.append(2)         # Número de pontos neste segmento (sempre 2)
        linhas.append(2 * i)     # Índice do ponto inicial
        linhas.append(2 * i + 1) # Índice do ponto final
    linhas = np.array(linhas)

    #criar nova malha/objeto de polydata
    poly = pv.PolyData(pontos, lines=linhas)

    #atribuir raio a cada ponto
    poly.point_data["raio"] = np.repeat(r, 2)
    return poly, r

#Função que gera os tubos dos segmentos
def gerar_tubos(estado):

    poly = estado["poly"] #objeto polyData
    r = estado["r_seg"]   #lista com raio de cada segmento
    escala = estado["escala"]  # Escala dos raio, proporcional

    #Se esatdo espessura ta ativado (inicialmente ta)
    if estado["espessura"]:
        r_vis = np.repeat(r, 2) * escala                    # raio de vizualização baseado na espessura
    #se não tiver ativado
    else:
        numero_total = 2 * len(r)  #numero de pontos que possuem raio
        media = r.mean() * escala  #media de espessura constante a todos
        r_vis = np.full(numero_total, media)  #matrix com valor constante a todos os pontos

    poly.point_data["raio_visual"] = r_vis

    # Aplica o filtro de tubos do PyVista para converter linhas em cilindros 3D
    tubos = poly.tube(scalars="raio_visual", absolute=True, n_sides=N_LADOS, capping=True)
    return tubos


#Função que desenha a arvore de arterias
def desenhar(plotter, estado, primeira_vez=False):
    #gerar os tubos
    tubos = gerar_tubos(estado)

    kw = dict(name="Arvore_CCO" , smooth_shading=True)
    if not primeira_vez:
        kw["reset_camera"] = False     # mantém a câmera do usuário

    #se o estado de cor está ativado (cor relacionada ao raio)    
    if estado["cor"]:
        plotter.add_mesh(tubos, 
                         scalars="raio", 
                         cmap=mapa_rgb(),
                         clim=(estado["rmin"], estado["rmax"]),
                         scalar_bar_args={"title": TITULO_BARRA, "fmt": "%.4f"}, 
                         **kw)
    #se não estiver ativada 
    else:
        try:
            plotter.remove_scalar_bar(TITULO_BARRA) #remove a barra de cores
        except Exception:
            pass
        plotter.add_mesh(
            tubos, 
            color="firebrick", 
            show_scalar_bar=False, 
            **kw
        )
    plotter.render()

#função que cria o botão de ativação do raio em função da cor e da espessura
def _botao(plotter, rotulo, chave, estado, y):
    def cb(valor):
        estado[chave] = bool(valor)
        desenhar(plotter, estado)
    plotter.add_checkbox_button_widget(cb, value=estado[chave], position=(10, y),
                                       size=32, color_on="green", color_off="grey")
    plotter.add_text(rotulo, position=(52, y + 6), font_size=10, name=f"rot_{chave}")


#Função principal
def read_and_config(plotter: pv.Plotter, path: str) -> dict:
    mesh = pv.read(path)                                  # arquivo é um polydata, entt mesh é um objeton pv.polydata

    #calcular atributos
    numero_pontos, numero_segmentos = obeter_atributos(mesh)
    nome_raio, raios, raio_min, raio_max = obter_raio(mesh)

    #Imprimir informações
    print(f"MODELO CARREGADO: {Path(path).name}")
    print(f"Número de pontos (vértices): {numero_pontos}")
    print(f"Número de segmentos (arestas): {numero_segmentos}")
    print(f"Atributo de raio: '{nome_raio}'")
    print(f"  - Raio mínimo: {raio_min:.7f}")
    print(f"  - Raio máximo: {raio_max:.7f}")


    poly, r_seg = montar_segmentos(mesh, raios, numero_segmentos)

    estado = {
        "mesh": mesh, "nome_raio": nome_raio, "raios": raios,
        "poly": poly, "r_seg": r_seg,
        "rmin": raio_min, "rmax": raio_max,
        # raios reais (~0.2-1.0) são enormes frente ao domínio (~0.05):
        # a escala leva o maior vaso a ~1.5% da diagonal, mantendo proporções.
        "escala": 0.015 * mesh.length / float(r_seg.max()),
        "cor": True, "espessura": True,
    }

    #desenha a arvore
    desenhar(plotter, estado, primeira_vez=True)

    #adicionar no topo as informações
    plotter.add_text(f"{Path(path).name}\npontos: {numero_pontos} | segmentos: {numero_segmentos}\n"
                     f"raio: [{raio_min:.7f}, {raio_max:.7f}]",
                     position="upper_left", font_size=9, name="info_modulo1")
    
    _botao(plotter, "Cor em função do raio", "cor", estado, 120)
    _botao(plotter, "Espessura em funcão do raio", "espessura", estado, 162)
    plotter.add_axes()

    if np.ptp(np.asarray(mesh.points)[:, 2]) < 1e-9 * max(mesh.length, 1e-12):
        plotter.view_xy()                                 # modelo 2D
    return estado


if __name__ == "__main__":
    #qual arquivo
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = "../../data/dados_modelos2D/tree2D_Nterm008.vtk"
        
    p = pv.Plotter()
    read_and_config(p, caminho)
    p.show()