import pyvista as pv
from typing import Literal
import numpy as np

# Verifica que ponto (x, y) está dentro em relação a borda analisada da área delimitada
def is_inside(point: tuple[float, float], edge_type: Literal["LEFT", "RIGHT", "BOTTOM", "TOP"], clip_value: float) -> bool:
    x, y = point

    if edge_type == "LEFT":
        return x >= clip_value
    elif edge_type == "RIGHT":
        return x <= clip_value
    elif edge_type == "BOTTOM":
        return y >= clip_value
    elif edge_type == "TOP":
        return y <= clip_value


def compute_intersection(point_1: tuple[float, float], point_2: tuple[float, float], edge_type: Literal["LEFT", "RIGHT", "TOP", "BOTTOM"], clip_value: float) -> tuple[float, float]:

    x_1, y_1 = point_1
    x_2, y_2 = point_2

    if edge_type == "LEFT" or edge_type == "RIGHT":
        x_int = float(clip_value)
        if abs(x_2 - x_1) < 1e-9:
            y_int = y_1
        else:
            t = (x_int - x_1) / (x_2 - x_1)
            y_int = y_1 + t * (y_2 - y_1)
        return (x_int, y_int) 

    elif edge_type == "BOTTOM" or edge_type == "TOP":
        y_int = float(clip_value)
        if abs(y_2 - y_1) < 1e-9:
            x_int = x_1
        else:
            t = (y_int - y_1) / (y_2 - y_1)
            x_int = x_1 + t * (x_2 - x_1)
        return (x_int, y_int)


def sutherland_hodgman_clip_edge(subject_polygon: list[tuple[float, float]], edge_type: Literal["BOTTOM", "LEFT", "RIGHT", "TOP"], clip_value: float) -> list[tuple[float, float]]:

    if len(subject_polygon) == 0:
        return []

    output_polygon = []
    point_prev = subject_polygon[-1]

    for point_curr in subject_polygon:
        curr_inside = is_inside(point_curr, edge_type, clip_value)
        prev_inside = is_inside(point_prev, edge_type, clip_value)

        if curr_inside and prev_inside:
            # De Dentro para Dentro, sem interceção
            output_polygon.append(point_curr)

        elif prev_inside and not curr_inside:
            # De Dentro para Fora, com interceção
            inter = compute_intersection(point_prev, point_curr, edge_type, clip_value)
            output_polygon.append(inter)

        elif not prev_inside and not curr_inside:
            # De Fora para Fora, sem interceção
            pass

        elif not prev_inside and curr_inside:
            # De Fora para Dentro, com interceção
            inter = compute_intersection(point_prev, point_curr, edge_type, clip_value)
            output_polygon.append(inter)
            output_polygon.append(point_curr)

        point_prev = point_curr

    return output_polygon
        

def sutherland_hodgman_clip(subject_polygon: list[tuple[float, float]], window: tuple[float, float, float, float]) -> tuple[list[tuple[float, float]], list[tuple[str, list[tuple[float, float]]]]]:
    x_min, y_min, x_max, y_max = window
    edges = [
        ("BOTTOM", y_min),
        ("RIGHT", x_max),
        ("TOP", y_max),
        ("LEFT", x_min)
    ]

    current_polygon = list(subject_polygon)
    history = [("Original", list(current_polygon))]

    for edge_type, clip_val in edges:
        current_polygon = sutherland_hodgman_clip_edge(current_polygon, edge_type, clip_val)
        history.append((f"Recorte {edge_type} ({clip_val})", list(current_polygon)))

    return current_polygon, history



# Cria malha a partir da lista de pontos fornecida
def contorno(pontos: list[tuple[float, float]], z: float = 0.0) -> pv.PolyData:

    p = np.array([(x, y, z) for x, y in pontos], dtype=float)
    n = len(p)
    malha = pv.PolyData(p)

    # Guarda informação para construir segmentos
    # [n + 1] -> numero de pontos + 1 para fechar o poligono
    # [0, 1, 2, ..., n, 0]

    malha.lines = np.hstack([[n + 1], np.arange(n), [0]])
    return malha

def recorte_interativo() -> None:

    # Atualiza e redesenha 
    def atualizar():
            # Encontra as 4 bordas do retangulo
            cx, cy, w, h = estado["cx"], estado["cy"], estado["w"], estado["h"]
            xmin, xmax, ymin, ymax = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2

            # Sutherland–Hodgman aplicado ao polígono inteiro
            resultado, _historico = sutherland_hodgman_clip(
                POLIGONO_TESTE, (xmin, ymin, xmax, ymax))
     
            # Desenha o poligono recortado em vermelho
            if len(resultado) >= 3:
                pl.add_mesh(contorno(resultado, 0.1), color="red", line_width=4,
                            lighting=False, name="saida_sh", reset_camera=False)
            else:
                pl.remove_actor("saida_sh")
     
            # Desenha o retangulo de corte em preto
            caixa = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
            pl.add_mesh(contorno(caixa, 0.2), color="black", line_width=2,
                        lighting=False, name="caixa", reset_camera=False)
     
            pl.render()

    # Converte a posição do mouse para as coordenadas reais
    def tela_para_mundo(x, y):
        r = pl.renderer
        r.SetDisplayPoint(x, y, 0)
        r.DisplayToWorld()
        wx, wy, _, ww = r.GetWorldPoint()
        return wx / ww, wy / ww

    # Ver se pressionou dentro do retangulo e ativa estado de arrastar
    def ao_pressionar(obj, _evento):
        x, y = tela_para_mundo(*obj.GetEventPosition())

        if abs(x - estado["cx"]) <= estado["w"] / 2 and abs(y - estado["cy"]) <= estado["h"] / 2:
            estado["arrastando"] = True
            estado["off_x"] = estado["cx"] - x
            estado["off_y"] = estado["cy"] - y

    # Atualiza posiçao do retangulo ao mover o mouse
    def ao_mover(obj, _evento):
        if not estado["arrastando"]:
            return
        x, y = tela_para_mundo(*obj.GetEventPosition())
        estado["cx"] = float(np.clip(x + estado["off_x"], -LIM_X, LIM_X))
        estado["cy"] = float(np.clip(y + estado["off_y"], -LIM_Y, LIM_Y))
        atualizar()

    # Desliga estado de arrastar
    def ao_soltar(_obj, _evento):
        estado["arrastando"] = False
    
    POLIGONO_CONVEXO = [(-7.0, -2.0), (-3, -6), (4, -6), (8, -1), (6, 5), (0, 8), (-5, 6) ]
 
    POLIGONO_TESTE = POLIGONO_CONVEXO

    # Atributos de informações do retangulo
    estado = {
        "cx": 3.5,
        "cy": 2.5,
        "w": 10.0,
        "h": 8.0,
        "arrastando": False,
        "off_x": 0,
        "off_y": 0,
    }

    # Limites para que a caixa não suma da tela
    LIM_X, LIM_Y = 15.0, 11.0    

    # Inicialização do Plotter
    pl = pv.Plotter(window_size=[1100, 850], title="Recorte de Poligonos")
 
    # Malha do polígono utilizado
    pl.add_mesh(contorno(POLIGONO_TESTE, 0.0), color="gray", line_width=2,)

 
    # Sem rotação de câmera (só zoom, sempre em 2D).
    pl.enable_image_style()

    # Atribui funções callbacks a eventos do mouse
    interactor = pl.iren.interactor
    interactor.AddObserver("LeftButtonPressEvent", ao_pressionar)
    interactor.AddObserver("MouseMoveEvent", ao_mover)
    interactor.AddObserver("LeftButtonReleaseEvent", ao_soltar)

    # Atualiza toda a imagem (aciona algoritmo e atualiza)
    atualizar()
    pl.camera_position = [(0, 0, 50), (0, 0, 0), (0, 1, 0)]
    pl.enable_parallel_projection()
    pl.camera.parallel_scale = 12       
    pl.camera.clipping_range = (1, 100)
 
    pl.show()

    

if __name__ == "__main__":
    recorte_interativo()