import pyvista as pv

from typing import Literal

def aliasing_widgets(plotter: pv.Plotter) -> None:
    def disable_antialising(value: bool) -> None:
        if value:
            plotter.disable_anti_aliasing()

    def enable_antialising(type: Literal["msaa", "fxaa", "ssaa"]) -> None:
        plotter.enable_anti_aliasing(type)

    plotter.add_radio_button_widget(
        callback= lambda: disable_antialising(True),
        radio_button_group= 'antialising',
        position= (1250, 560),
        title= "Sem Antialising",
        value= False,
        size= 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: enable_antialising("msaa"),
        radio_button_group = 'antialising',
        position= (1250, 500),
        title= "MSAA",
        value= True,
        size= 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: enable_antialising("fxaa"),
        radio_button_group= 'antialising',
        position= (1250, 440),
        title= "FXAA",
        value= False,
        size= 25,
    )

    plotter.add_radio_button_widget(
        callback= lambda: enable_antialising("ssaa"),
        radio_button_group= 'antialising',
        position= (1250, 380),
        title= "SSAA",
        value= False,
        size= 25,
    )

