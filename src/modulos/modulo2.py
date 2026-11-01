# Widget com opçoes de vista pré-definidas
# Widget para escolha entre projeção ortográfica ou perspectiva

import pyvista as pv


def view_widgets(plotter: pv.Plotter) -> None:
    def set_projection(value: bool) -> None:
        plotter.disable_parallel_projection() if value else plotter.enable_parallel_projection()
         

    def set_view(pos: str) -> None:
        plotter.camera_position = pos
         

    # Editar posicionamento para ser de acordo com o tamanho da janela atual
    plotter.add_radio_button_widget(
        callback = lambda: set_projection(True),
        radio_button_group= 'projection',
        position=(00.0, 720.0),
        title='Projeção ortogonal',
        value=True,
        size = 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: set_projection(False),
        radio_button_group= 'projection',
        position=(00.0, 660.0),
        title='Projeção Paralela',
        value=False,
        size = 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: set_view('yz'),
        radio_button_group= 'view',
        position=(790.0, 720.0),
        title='Vista Frontal',
        value=True,
        size= 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: set_view('xz'),
        radio_button_group= 'view',
        position=(790.0, 660.0),
        title='Vista Lateral',
        value= False,
        size= 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: set_view('xy'),
        radio_button_group= 'view',
        position=(790.0, 600.0),
        title='Vista Superior',
        value=False,
        size=25,
    )
