# Módulo 6 - Recorte de segmentos de reta 
#
# Teste isolado (a partir de src/):
#     python3 modulos/modulo6.py ../data/dados_modelos2D/tree2D_Nterm032.vtk
#
# O que faz:
#  1. Implementa Cohen-Sutherland (obrigatório) e Liang-Barsky (o 2º algoritmo escolhido).
#  2. Define uma janela de recorte retangular sobre a árvore e recorta os segmentos
#     da árvore com o algoritmo escolhido.
#  3. Mostra: janela, partes mantidas (verde) e partes descartadas (vermelho).
#  4. Botões: escolher o algoritmo, ligar/desligar o recorte e mudar o tamanho da janela.
#  5. Compara os algoritmos (nº de interseção, divisões, segmentos aceitos/cortados/rejeitados)
#     e salva imagens antes e depois do recorte em report/figures/.

from pathlib import Path
import sys

import numpy as np
import pyvista as pv

import matplotlib
matplotlib.use("Agg")                      
import matplotlib.pyplot as plt

from var_global import PATH_FILE_MOD6


# Bits dos códigos de região (Cohen-Sutherland):  ACIMA | ABAIXO | DIREITA | ESQUERDA
ESQUERDA = 1   # 0001
DIREITA = 2    # 0010
ABAIXO = 4     # 0100
ACIMA = 8      # 1000

DESLOCAMENTO_Z = 0.02          #levanta as linhas verdes/vermelhas acima dos tubos
TAMANHO_INICIAL_JANELA = 0.5   # janela começa com 50% da largura e da altura da arvore

# posições dos widgets
POSICAO_Y_BOTAO_ALGORITMO = 210
POSICAO_Y_BOTAO_RECORTE = 252
POSICAO_SLIDER = ((0.62, 0.20), (0.97, 0.20))



# Parte 1: algoritmos de recorte
def somar(contadores, nome):
    # soma 1 em um contador (cria o contador se ele ainda não existir)
    if contadores is not None:
        contadores[nome] = contadores.get(nome, 0) + 1


def calcular_codigo_regiao(x, y, janela):
    # Código de 4 bits do ponto (x, y). 0000 significa que o ponto está DENTRO da janela.
    x_min, y_min, x_max, y_max = janela
    codigo = 0
    if x < x_min:
        codigo = codigo | ESQUERDA     # '|' (OR bit a bit) liga o bit
    elif x > x_max:
        codigo = codigo | DIREITA
    if y < y_min:
        codigo = codigo | ABAIXO
    elif y > y_max:
        codigo = codigo | ACIMA
    return codigo


#Funçõa que recorta pelo método Cohen Sutherland
def cohen_sutherland(x1, y1, x2, y2, janela, contadores=None, mostrar_passos=False):
    # Retorna (visivel, x1, y1, x2, y2). Se visivel for False, as coordenadas devem ser ignoradas.
    x_min, y_min, x_max, y_max = janela
    codigo1 = calcular_codigo_regiao(x1, y1, janela)
    codigo2 = calcular_codigo_regiao(x2, y2, janela)

    while True:
        if mostrar_passos:
            print(f"   P1=({x1:.2f},{y1:.2f}) [{codigo1:04b}]  P2=({x2:.2f},{y2:.2f}) [{codigo2:04b}]")

        # Caso 1: aceitação trivial -> os dois pontos estão dentro (OR dá 0000)
        if (codigo1 | codigo2) == 0:
            if mostrar_passos:
                print("   -> aceitação trivial")
            return True, x1, y1, x2, y2

        # Caso 2: rejeição trivial -> os dois pontos estão fora do MESMO lado (AND diferente de 0)
        if (codigo1 & codigo2) != 0:
            if mostrar_passos:
                print("   -> rejeição trivial")
            return False, x1, y1, x2, y2

        # Caso 3: precisa recortar. 
        # Escolhe um ponto que esteja fora da janela.
        if codigo1 != 0:
            ponto1_esta_fora = True
            codigo_fora = codigo1
        else:
            ponto1_esta_fora = False
            codigo_fora = codigo2

        # Calcula onde o segmento cruza a borda indicada pelo código (uma borda por vez)
        if codigo_fora & ACIMA:                       # '&' (AND bit a bit) testa se o bit está ligado
            x_novo = x1 + (x2 - x1) * (y_max - y1) / (y2 - y1)
            y_novo = y_max
            borda = "ACIMA"
        elif codigo_fora & ABAIXO:
            x_novo = x1 + (x2 - x1) * (y_min - y1) / (y2 - y1)
            y_novo = y_min
            borda = "ABAIXO"
        elif codigo_fora & DIREITA:
            y_novo = y1 + (y2 - y1) * (x_max - x1) / (x2 - x1)
            x_novo = x_max
            borda = "DIREITA"
        else:                                         # sobrou ESQUERDA
            y_novo = y1 + (y2 - y1) * (x_min - x1) / (x2 - x1)
            x_novo = x_min
            borda = "ESQUERDA"
        somar(contadores, "interseccoes")
        somar(contadores, "divisoes")                 # cada interseção gasta 1 divisão
        if mostrar_passos:
            print(f"   -> recorte na borda {borda}: ({x_novo:.2f},{y_novo:.2f})")

        # Troca o ponto que estava fora pelo ponto da interseção e recalcula o código 
        if ponto1_esta_fora:
            x1 = x_novo
            y1 = y_novo
            codigo1 = calcular_codigo_regiao(x1, y1, janela)
        else:
            x2 = x_novo
            y2 = y_novo
            codigo2 = calcular_codigo_regiao(x2, y2, janela)

#função que recorta pelo metodo Liang Barsky
def liang_barsky(x1, y1, x2, y2, janela, contadores=None, mostrar_passos=False):
    # Retorna (visivel, x1, y1, x2, y2). Usa P(t) = P1 + t*(P2 - P1), com t entre 0 e 1.
    x_min, y_min, x_max, y_max = janela
    dx = x2 - x1
    dy = y2 - y1

    t_entrada = 0.0     # maior valor de t em que o segmento ENTRA na janela
    t_saida = 1.0       # menor valor de t em que o segmento SAI da janela

    # Para cada borda k:  t * p[k] <= q[k]
    lista_p = [-dx, dx, -dy, dy]
    lista_q = [x1 - x_min, x_max - x1, y1 - y_min, y_max - y1]
    nomes = ["ESQUERDA", "DIREITA", "ABAIXO", "ACIMA"]

    for k in range(4):
        p = lista_p[k]
        q = lista_q[k]

        if p == 0:
            # segmento paralelo à borda k
            if q < 0:
                if mostrar_passos:
                    print(f"   {nomes[k]}: p=0 e q={q:.2f}<0 -> paralelo e FORA, rejeita")
                return False, x1, y1, x2, y2
            if mostrar_passos:
                print(f"   {nomes[k]}: p=0 e q={q:.2f}>=0 -> paralelo e dentro, ignora")
        else:
            r = q / p
            somar(contadores, "divisoes")
            if p < 0:
                # entrando na janela por esta borda -> sobe o limite inferior
                if r > t_saida:
                    if mostrar_passos:
                        print(f"   {nomes[k]}: ENTRANDO r={r:.4f} > t_saida={t_saida:.4f} -> rejeita")
                    return False, x1, y1, x2, y2
                if r > t_entrada:
                    t_entrada = r
            else:
                # saindo da janela por esta borda -> desce o limite superior
                if r < t_entrada:
                    if mostrar_passos:
                        print(f"   {nomes[k]}: SAINDO r={r:.4f} < t_entrada={t_entrada:.4f} -> rejeita")
                    return False, x1, y1, x2, y2
                if r < t_saida:
                    t_saida = r
            if mostrar_passos:
                print(f"   {nomes[k]}: p={p:.2f} q={q:.2f} r={r:.4f} -> t_entrada={t_entrada:.4f} t_saida={t_saida:.4f}")

    # sobreviveu as 4 bordas: calcula os novos extremos
    novo_x1 = x1 + t_entrada * dx
    novo_y1 = y1 + t_entrada * dy
    novo_x2 = x1 + t_saida * dx
    novo_y2 = y1 + t_saida * dy
    if mostrar_passos:
        print(f"   -> visível entre t={t_entrada:.4f} e t={t_saida:.4f}")
    return True, novo_x1, novo_y1, novo_x2, novo_y2


#funçãpo que escolhe o algoruitmo a ser usado pelo nome
def recortar_segmento(algoritmo, x1, y1, x2, y2, janela, contadores=None, mostrar_passos=False):
    # Escolhe o algoritmo pelo nome: "cohen" ou "liang"
    if algoritmo == "cohen":
        return cohen_sutherland(x1, y1, x2, y2, janela, contadores, mostrar_passos)
    return liang_barsky(x1, y1, x2, y2, janela, contadores, mostrar_passos)



# Parte 2: aplicar o recorte na árvore
def obter_segmentos(malha):
    # Lista de segmentos (x1, y1, z1, x2, y2, z2) lidos da malha.
    pontos = np.asarray(malha.points)
    segmentos = []
    for i in range(malha.n_cells):
        ids = list(malha.get_cell(i).point_ids)       # ids dos pontos da célula i
        for j in range(len(ids) - 1):
            a = pontos[ids[j]]
            b = pontos[ids[j + 1]]
            segmentos.append((a[0], a[1], a[2], b[0], b[1], b[2]))
    return segmentos


def calcular_janela(limites, fator):
    # Janela retangular centrada na árvore
    x_min, x_max, y_min, y_max = limites
    centro_x = (x_min + x_max) / 2
    centro_y = (y_min + y_max) / 2
    meia_largura = fator * (x_max - x_min) / 2
    meia_altura = fator * (y_max - y_min) / 2
    return (centro_x - meia_largura, centro_y - meia_altura,
            centro_x + meia_largura, centro_y + meia_altura)


def interpolar_z(x1, y1, z1, x2, y2, z2, x, y):
    # Descobrir o z de um ponto (x, y) que estar sobre o segmento original, para modulos 3d
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) >= abs(dy):
        if dx == 0:
            return z1               # segmento de tamanho zero
        t = (x - x1) / dx
    else:
        t = (y - y1) / dy
    return z1 + t * (z2 - z1)


def pontos_diferentes(xa, ya, xb, yb, tolerancia):
    return abs(xa - xb) > tolerancia or abs(ya - yb) > tolerancia


def recortar_todos(segmentos, janela, algoritmo):
    # Recorta todos os segmentos. Retorna (mantidos, descartados, resumo).
    # mantidos / descartados: listas de pares de pontos 3D ((x,y,z), (x,y,z)).
    contadores = {}
    mantidos = []
    descartados = []
    total_rejeitados = 0
    total_inteiros = 0       # aceitos sem precisar cortar
    total_cortados = 0       # aceitos, mas só uma parte

    x_min, y_min, x_max, y_max = janela
    tolerancia = 1e-9 * max(x_max - x_min, y_max - y_min)

    for segmento in segmentos:
        x1, y1, z1, x2, y2, z2 = segmento
        visivel, cx1, cy1, cx2, cy2 = recortar_segmento(algoritmo, x1, y1, x2, y2, janela, contadores)

        if not visivel:
            descartados.append(((x1, y1, z1), (x2, y2, z2)))
            total_rejeitados += 1
            continue

        cz1 = interpolar_z(x1, y1, z1, x2, y2, z2, cx1, cy1)
        cz2 = interpolar_z(x1, y1, z1, x2, y2, z2, cx2, cy2)
        mantidos.append(((cx1, cy1, cz1), (cx2, cy2, cz2)))

        foi_cortado = False
        if pontos_diferentes(x1, y1, cx1, cy1, tolerancia):    # pedaço antes do ponto recortado
            descartados.append(((x1, y1, z1), (cx1, cy1, cz1)))
            foi_cortado = True
        if pontos_diferentes(cx2, cy2, x2, y2, tolerancia):    # pedaço depois do ponto recortado
            descartados.append(((cx2, cy2, cz2), (x2, y2, z2)))
            foi_cortado = True
        if foi_cortado:
            total_cortados += 1
        else:
            total_inteiros += 1

    resumo = {"algoritmo": algoritmo, "total": len(segmentos),
              "inteiros": total_inteiros, "cortados": total_cortados,
              "rejeitados": total_rejeitados,
              "interseccoes": contadores.get("interseccoes", 0),
              "divisoes": contadores.get("divisoes", 0)}
    return mantidos, descartados, resumo


def texto_resumo(resumo):
    if resumo["algoritmo"] == "cohen":
        nome = "Cohen-Sutherland"
    else:
        nome = "Liang-Barsky"
    return (f"{nome}\n"
            f"segmentos: {resumo['total']} | dentro: {resumo['inteiros']} | "
            f"cortados: {resumo['cortados']} | rejeitados: {resumo['rejeitados']}\n"
            f"interseções: {resumo['interseccoes']} | divisões: {resumo['divisoes']}")



# Parte 3: desenho
def montar_linhas(lista_de_pares, deslocamento_z):
    # transformar uma lista de pares de pontos em UMA malha de linhas (ou None se a lista é vazia).
    if len(lista_de_pares) == 0:
        return None
    pontos = []
    linhas = []
    for i in range(len(lista_de_pares)):
        ponto_a, ponto_b = lista_de_pares[i]
        pontos.append([ponto_a[0], ponto_a[1], ponto_a[2] + deslocamento_z])
        pontos.append([ponto_b[0], ponto_b[1], ponto_b[2] + deslocamento_z])
        linhas.append(2)            # cada linha tem 2 pontos
        linhas.append(2 * i)        # índice do ponto inicial
        linhas.append(2 * i + 1)    # índice do ponto final
    return pv.PolyData(np.array(pontos), lines=np.array(linhas))


def remover_ator(plotter, nome):
    try:
        plotter.remove_actor(nome)
    except Exception:
        pass                       


def desenhar_resultado(plotter, estado6):
    janela = calcular_janela(estado6["limites_xy"], estado6["fator_janela"])
    x_min, y_min, x_max, y_max = janela
    z = estado6["z_topo"]

    # contorno da janela (5 pontos: o ultimo repete o primeiro para fechar o retangulo)
    pontos_janela = np.array([[x_min, y_min, z], [x_max, y_min, z], [x_max, y_max, z],
                              [x_min, y_max, z], [x_min, y_min, z]])
    contorno = pv.PolyData(pontos_janela)
    contorno.lines = np.hstack([[5], np.arange(5)])
    plotter.add_mesh(contorno, color="orange", line_width=4, name="m6_janela", reset_camera=False)

    if not estado6["usar_liang"] and not estado6["usar_cohen"]:
        remover_ator(plotter, "m6_mantido")
        remover_ator(plotter, "m6_descartado")
        plotter.add_text("Recorte desligado", position="lower_right", font_size=9, name="info_modulo6")
        plotter.render()
        return
    
    #definir qual algoritm
    if estado6["usar_liang"]:
        algoritmo_ativo = "liang" 
    else:
        algoritmo_ativo = "cohen"

    mantidos, descartados, resumo = recortar_todos(estado6["segmentos"], janela, algoritmo_ativo)
    estado6["resumo"] = resumo

    linhas_mantidas = montar_linhas(mantidos, 0.0)
    linhas_descartadas = montar_linhas(descartados, 0.0)

    #linhas mantidas de verde
    if linhas_mantidas is not None:
        plotter.add_mesh(linhas_mantidas, color="lime", line_width=5, name="m6_mantido", reset_camera=False)
    else:
        remover_ator(plotter, "m6_mantido")
    #linhas descartadas de vermelho
    if linhas_descartadas is not None:
        plotter.add_mesh(linhas_descartadas, color="red", line_width=2, name="m6_descartado", reset_camera=False)
    else:
        remover_ator(plotter, "m6_descartado")

    plotter.add_text(texto_resumo(resumo), position="lower_right", font_size=9, name="info_modulo6")
    plotter.render()


#função principal
def clipping_line_region(plotter: pv.Plotter, estado: dict = None) -> dict:
    if estado is None or "mesh" not in estado:
        print("[Módulo 6] precisa do 'estado' do módulo 1:  clipping_line_region(plotter, estado)")
        return None

    malha = estado["mesh"]
    x_min, x_max, y_min, y_max, z_min, z_max = malha.bounds
    segmentos = obter_segmentos(malha)
    # as linhas verdes/vermelhas ficam um pouco a frente da arvore para não ficarem escondidas nos tubos
    z_topo = z_max + DESLOCAMENTO_Z * malha.length

    # os segmentos das linhas verdes/vermelhas tambm precisam subir em z
    segmentos_elevados = []
    for s in segmentos:
        segmentos_elevados.append((s[0], s[1], s[2] + DESLOCAMENTO_Z * malha.length,
                                   s[3], s[4], s[5] + DESLOCAMENTO_Z * malha.length))

    #estado inicial, o cohen é ligado por default
    estado6 = {"segmentos": segmentos_elevados, "limites_xy": (x_min, x_max, y_min, y_max),
               "z_topo": z_topo, "fator_janela": TAMANHO_INICIAL_JANELA,
               "usar_cohen": True, "usar_liang": False, "resumo": None}

    # variaveis para armazenar referencias aos widgets de botão
    widget_liang = {"ref": None}
    widget_cohen = {"ref": None}

    # botão 1: escolhe o algoritmo (ligado = Liang)
    def ao_clicar_algoritmo(ligado):
        if ligado:
            estado6["usar_liang"] = True
            estado6["usar_cohen"] = False #se liga um, desliga o outro
            
            if widget_cohen["ref"] is not None:
                widget_cohen["ref"].GetRepresentation().SetState(0)

        else:
            estado6["usar_liang"] = False
        desenhar_resultado(plotter, estado6)
        print("[Módulo 6]", texto_resumo(estado6["resumo"]).replace("\n", " | "))

    #se tiver a referência do widget do cohan, força o estado visual para desligado (False)
    b1 = plotter.add_checkbox_button_widget(ao_clicar_algoritmo, value=False,
                                       position=(10, POSICAO_Y_BOTAO_ALGORITMO),
                                       size=32, color_on="green", color_off="grey")
    widget_liang["ref"] = b1
    plotter.add_text("Usar Liang-Barsky",
                     position=(52, POSICAO_Y_BOTAO_ALGORITMO + 6), font_size=10, name="rot_m6_algoritmo")

    #botão 2: liga Cohen-Sutherland
    def ao_clicar_recorte(ligado):
        if ligado:
            estado6["usar_cohen"] = True
            estado6["usar_liang"] = False  #se liga um, desliga o outro
            # Se tiver a referência do widget do Liang, força o estado visual para desligado (False)
            if widget_liang["ref"] is not None:
                widget_liang["ref"].GetRepresentation().SetState(0)
        else:
            estado6["usar_cohen"] = False
        desenhar_resultado(plotter, estado6)
        if estado6["resumo"]:
            print("[Módulo 6]", texto_resumo(estado6["resumo"]).replace("\n", " | "))

    b2 = plotter.add_checkbox_button_widget(ao_clicar_recorte, value=True,
                                       position=(10, POSICAO_Y_BOTAO_RECORTE),
                                       size=32, color_on="green", color_off="grey")

    widget_cohen["ref"] = b2
    plotter.add_text("Usar Cohen-Sutherland",
                     position=(52, POSICAO_Y_BOTAO_RECORTE + 6), font_size=10, name="rot_m6_recorte")

    #slider: tamanho da janela
    def ao_mudar_tamanho(valor):
        estado6["fator_janela"] = float(valor)
        desenhar_resultado(plotter, estado6)

    plotter.add_slider_widget(ao_mudar_tamanho, [0.1, 1.2], value=TAMANHO_INICIAL_JANELA,
                              title="Tamanho da janela de recorte",
                              pointa=POSICAO_SLIDER[0], pointb=POSICAO_SLIDER[1], style="modern")

    desenhar_resultado(plotter, estado6)
    return estado6



# figuras antes e depois dos cortes
def salvar_figura_comparacao(segmentos, janela, caminho_saida, titulo):
    # 3 painéis: antes | depois (Cohen-Sutherland) | depois (Liang-Barsky)

    x_min, y_min, x_max, y_max = janela
    figura, eixos = plt.subplots(1, 3, figsize=(16, 5.5))
    titulos = ["Antes do recorte", "Depois - Cohen-Sutherland", "Depois - Liang-Barsky"]

    for i in range(3):
        eixo = eixos[i]
        eixo.set_title(titulos[i])
        # janela de recorte
        eixo.plot([x_min, x_max, x_max, x_min, x_min], [y_min, y_min, y_max, y_max, y_min],
                  color="orange", linewidth=2)
        for segmento in segmentos:
            x1, y1, z1, x2, y2, z2 = segmento
            if i == 0:
                eixo.plot([x1, x2], [y1, y2], color="dimgray", linewidth=1.2)
            else:
                eixo.plot([x1, x2], [y1, y2], color="darkgray", linewidth=1.0, linestyle="--")
                if i == 1:
                    visivel, cx1, cy1, cx2, cy2 = recortar_segmento("cohen", x1, y1, x2, y2, janela)
                else:
                    visivel, cx1, cy1, cx2, cy2 = recortar_segmento("liang", x1, y1, x2, y2, janela)
                if visivel:
                    eixo.plot([cx1, cx2], [cy1, cy2], color="green", linewidth=2.5)
        eixo.set_aspect("equal")
    figura.suptitle(titulo)
    figura.tight_layout()
    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(caminho_saida, dpi=150)
    plt.close(figura)
    print(f"Figura salva em: {caminho_saida}")



if __name__ == "__main__":
    pasta = Path(__file__).resolve().parents[2] / "report" / "figures"

    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        caminho = PATH_FILE_MOD6

    malha = pv.read(caminho)
    segmentos_arvore = obter_segmentos(malha)
    janela_figura = calcular_janela(malha.bounds[0:4], TAMANHO_INICIAL_JANELA)
    salvar_figura_comparacao(segmentos_arvore, janela_figura,
                             pasta / f"modulo6_{Path(caminho).stem}.png",
                             f"Árvore CCO ({Path(caminho).name}): recorte dos segmentos")

    p = pv.Plotter()
    p.add_mesh(malha, color="firebrick", line_width=2) 
    clipping_line_region(p, {"mesh": malha})
    p.view_xy()
    p.show()