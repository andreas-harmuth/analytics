import pygal
from pygal.style import Style
import numpy as np
from analytics.wl_to_rbg import wavelength_to_rgb

def plot_data(spectra,lasers):
    wl_list = []
    # Ugly double loop
    for data in spectra:
        name = (list(data.keys())[0])

        # Coding so good, not lazy
        wl_list.append('rgb'+str(wavelength_to_rgb(data[name][:,0][np.argmax(data[name][:,2])])))
        wl_list.append('rgb' + str(wavelength_to_rgb(data[name][:, 0][np.argmax(data[name][:, 2])])))


    for i in lasers:
        wl_list.append('rgb(130,130,130)')



    custom_style = Style(
        opacity='.6',
        opacity_hover='.9',
        transition='400ms ease-in',
        plot_background='transparent',
        foreground_subtle='#D1DAE3',
        colors=wl_list)
    xy_chart = pygal.XY(style=custom_style,max_scale=6)



    for data in spectra:
        name = (list(data.keys())[0])
        coord1 = []
        coord2 = []
        for row in data[name]:
            if row[2] > 0:
                coord1.append((row[0],row[2]))
            if row[1] > 0:
                coord2.append((row[0], row[1]))
        xy_chart.add(name, coord1,fill=True,interpolate='cubic',show_dots=False,dots_size=0)
        xy_chart.add(None, coord2, show_dots=False,stroke_style={'width': 0.5, 'dasharray': '3'})

    for wl in lasers:
        xy_chart.add('Laser: '+str(wl), [(wl,0),(wl,100)], show_dots=False, stroke_style={'width': 0.7, 'dasharray': '6'})

    xy_chart.render_to_file('./chart.svg')

    return xy_chart.render_data_uri()