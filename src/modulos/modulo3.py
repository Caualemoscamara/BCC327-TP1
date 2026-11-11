import pyvista as pv
import numpy as np
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Algoritmo DDA
def dda_line(x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
    dx = x2 - x1
    dy = y2 - y1
    
    # Número de passos é determinado pela maior variação (|dx| ou |dy|)
    steps = int(max(abs(dx), abs(dy)))
    
    if steps == 0:
        return [(round(x1), round(y1))]
    
    x_inc = dx / steps
    y_inc = dy / steps
    
    x = float(x1)
    y = float(y1)
    
    pixels = []
    for _ in range(steps + 1):
        pixels.append((round(x), round(y)))
        x += x_inc
        y += y_inc
        
    return pixels

def bresenham_line(x_1: int, y_1: int, x_2: int, y_2: int) -> list[tuple[int, int]]:
    dx = abs(x_2 - x_1)
    dy = abs(y_2 - y_1)

    step_x = 1 if x_1 < x_2 else -1
    step_y = 1 if y_1 < y_2 else -1

    x, y = x_1, y_1
    pixels = [(x, y)]

    if dx >= dy:
        p = 2 * dy - dx
        for _ in range(dx):
            x += step_x
            if p >= 0:
                y += step_y
                p += 2 * (dy - dx)
            else:
                p += 2 * dy
            pixels.append((x, y))
    else:
        p = 2 * dx - dy
        for _ in range(dy):
            y += step_y
            if p >= 0:
                x += step_x
                p += 2* (dx - dy)
            else:
                p += 2 * dx
            pixels.append((x, y))

    return pixels

def plot_rasterization_comparison(segments: list[tuple[tuple[int, int], tuple[int, int]]], margem:int = 2) -> None:

    segs = []

    # Rotula cada segmento de reta
    for i, seg in enumerate(segments):
        p1, p2 = seg[0], seg[1]
        rotulo = seg[2] if len(seg) > 2 else f"reta {i + 1}"
        segs.append((p1, p2, rotulo))

    todas_x = [c for p1, p2, _ in segs for c in (p1[0], p2[0])]
    todas_y = [c for p1, p2, _ in segs for c in (p1[1], p2[1])]
    x_min, x_max = min(todas_x) - margem, max(todas_x) + margem
    y_min, y_max = min(todas_y) - margem, max(todas_y) + margem

    largura = x_max - x_min + 1
    altura = y_max - y_min + 1
    escala = max(largura, altura)

    fig_lado = min(max(8, escala * 0.4), 18)
    fig, ax = plt.subplots(figsize=(fig_lado, fig_lado))

    # Grade de pixels (linhas menores entre os pixels)
    ax.set_xticks(np.arange(x_min - 0.5, x_max + 1, 1), minor=True)
    ax.set_yticks(np.arange(y_min - 0.5, y_max + 1, 1), minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.6)
 
    # Rótulos dos eixos em passos legíveis
    passo = max(1, int(escala // 20))
    ax.set_xticks(np.arange(x_min, x_max + 1, passo))
    ax.set_yticks(np.arange(y_min, y_max + 1, passo))
    ax.tick_params(which='minor', length=0)
 
    # Uma cor por reta
    cmap = plt.get_cmap('tab10')
    handles_retas = []
        
    for i, (p1, p2, rotulo) in enumerate(segs):
        cor = cmap(i%10)
        x1, y1 = p1
        x2, y2 = p2
        
        # Obter pixels dos dois algoritmos
        dda_pixels = dda_line(x1, y1, x2, y2)
        bres_pixels = bresenham_line(x1, y1, x2, y2)
        
        # Destacar os pixels calculados por Bresenham
        for px, py in bres_pixels:
            rect = plt.Rectangle((px - 0.5, py - 0.5), 1, 1, facecolor=cor, alpha=0.35, edgecolor=cor, linewidth=1)
            ax.add_patch(rect)
                
        # Marcar os centros dos pixels do DDA
        dda_x = [p[0] for p in dda_pixels]
        dda_y = [p[1] for p in dda_pixels]
        ax.plot(dda_x, dda_y, 'o', color=cor, markeredgecolor='black', markeredgewidth=0.6, markersize = 4)
        
        # Desenhar a linha matemática contínua ideal
        ax.plot([x1, x2], [y1, y2], '--',color=cor,  linewidth=1.8)
        
        # Destacar pontos inicial e final
        ax.plot([x1, x2], [y1, y2], 's', color='white', markeredgecolor=cor,
                markeredgewidth=2, markersize=8)

        handles_retas.append(
            Line2D([0], [0], color=cor, linewidth=3,
                   label=f"{rotulo}: ({x1},{y1}) → ({x2},{y2})")
        )

    # Config visual de legenda
    handles_estilo = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', alpha=0.5,
               markersize=10, label='Bresenham (pixel)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=6, label='DDA (round)'),
        Line2D([0], [0], color='gray', linestyle='--', label='Linha contínua ideal'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='white',
               markeredgecolor='gray', markeredgewidth=2, markersize=8,
               label='Extremidades'),
        ]

    ax.legend(handles=handles_retas + handles_estilo, loc='upper left',
              bbox_to_anchor=(1.02, 1), fontsize=8, borderaxespad=0)


    # Config dos graficos (labels, limites, titulos)
    ax.set_xlim(x_min - 0.5, x_max - 0.5)
    ax.set_ylim(y_min -0.5, y_max - 0.5)
    ax.set_aspect('equal')
    ax.set_title(f"{len(segs)}\n$P_1=({x1},{y1})$, $P_2=({x2},{y2})$", fontsize=11, fontweight='bold')
    ax.set_xlabel('X (colunas)')
    ax.set_ylabel('Y (linhas)')


    plt.tight_layout()    
    
    # Salva graficos em imagem
    output_out = "rasterizacao_linhas.png"
    plt.savefig(output_out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Gráfico {output_out} gerado e salvo em seu diretório.")

# Junta informações de pontos (convertidos para inteiros) com relação nos segmentos -> Cria vetor de segmentos
def points_to_segments(lines: np.ndarray, points: np.ndarray, qnt: int) -> list[tuple[tuple[int, int]]]:
    segments = []

    for j in range(0, qnt * 3  , 3):
        p1_x, p1_y = points[lines[j+1]][0], points[lines[j+1]][1]
        p2_x, p2_y = points[lines[j+2]][0], points[lines[j+2]][1]

        p1_x = math.ceil((p1_x * 500))
        p1_y = math.ceil((p1_y * 500))
        p2_x = math.ceil((p2_x * 500))
        p2_y = math.ceil((p2_y * 500))

        segments.append([(p1_x, p1_y), (p2_x, p2_y)])

    return segments

# Controle da rasterizaco.
# Lê dados -> cria lista de segmentos -> Aplica diferentes algoritmos para cada segmento
def rasterizacao_linhas(path: str) -> None:
    print("Running rasterização de linhas 2D")

    mesh = pv.read(path)
    lines = mesh.lines
    points = mesh.points

    segmentos = points_to_segments(lines, points, 20)


    for i, seg in enumerate(segmentos):
        p1, p2 = seg[0], seg[1]

        bres = bresenham_line(*p1, *p2)
        dda = dda_line(*p1, *p2)
 

    plot_rasterization_comparison(segmentos)
 
    print("\n Rasterização de linhas concluída com sucesso.")



