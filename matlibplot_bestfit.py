import json

from analytics.wl_to_rbg import wavelength_to_rgb
import matplotlib.pyplot as plt, mpld3
import numpy as np
import seaborn as sns


def calibrate_data(M,precision = 10):
    total_p = np.sum(M[:,2])
    new_data = []
    for i,wv in enumerate(M[:,0]):
        rel_p = M[:,0][i]/total_p
        new_data.extend([wv]*(rel_p*precision))

    print(new_data)





def matplot_data(spectra,lasers,pre_data=False):
    sns.set(color_codes=True) #?

    wl_list = []

    if pre_data:
        spectra = json.loads(spectra[0]) # Load the set from the db in json format --> dict
        new_spectra = []
        for data in spectra:
            new_spectra.append({data:np.column_stack((spectra[data]['wavelength'],spectra[data]['emission'],spectra[data]['rel_emission']))})
        spectra = new_spectra


    # Ugly double loop
    for data in spectra:
        name = (list(data.keys())[0])

        # Coding so good, not lazy
        wl_list.append('rgb'+str())
        wl_list.append('rgb' + str(wavelength_to_rgb(data[name][:, 0][np.argmax(data[name][:, 2])])))


    for i in lasers:
        wl_list.append('rgb(130,130,130)')

    x = list(spectra[0].items())[0][1][:,0]
    # Init the main graph
    #ax = sns.distplot(x)

    fig = plt.figure(figsize=(10, 6))

    fig.patch.set_facecolor('blue')
    fig.patch.set_alpha(0.7)

    ax = fig.add_subplot(111)

    font = {'family' : 'monospace',
            'weight' : 'black',
            'color': '#242424',
            'size': 10,
            'horizontalalignment': 'center',
            'verticalalignment': 'center'
            }

    legend_list = []
    for debug, data in enumerate(spectra):
        name = (list(data.keys())[0])

        max_em_i = np.argmax(data[name][:, 2])
        max_wl = data[name][:, 0][max_em_i]
        ax.fill_between(data[name][:,0].tolist(), [val if val > 0 else 0 for val in data[name][:,2]],
                         color=tuple(color/255 for color in wavelength_to_rgb(max_wl)),
                         alpha=.5)

        ax.plot(data[name][:,0].tolist(), [val if val > 0 else 0 for val in data[name][:,1]],':',linewidth=0.8,
                         color=tuple(color/255 for color in wavelength_to_rgb(data[name][:,0][np.argmax(data[name][:,2])])),
                         alpha=.7)

        #ax.text(max_wl, (data[name][:, 2][max_em_i])/3, name, fontdict=font,rotation=90)
        ax.text(max_wl, 30, name, fontdict=font, rotation=90)
        legend_list.append(name)

    #plt.legend(legend_list) # TODO: doesn't work in html

    for laser in lasers:
            #ax.vlines(x=laser,0,100,colors='r', linestyles='--')

            ax.plot([laser,laser],[0,100],linestyle='--',color='grey',linewidth=0.8)
            ax.text(laser, 95, str(laser)+" nm", fontdict=font,rotation=45)
        #sns.kdeplot(x, calibrate_data(data[name]), bw=.2, label=name, shade=True, color=tuple(color/255 for color in wavelength_to_rgb(data[name][:,0][np.argmax(data[name][:,2])])))

            #ax.vlines(xlaser, ymin=0, ymax=max(y_data), color='red', zorder=2)
            #if row[1] > 0:
            #    coord2.append((row[0], row[1]))


    #for wl in lasers:
        #xy_chart.add('Laser: '+str(wl), [(wl,0),(wl,100)], show_dots=False, stroke_style={'width': 0.7, 'dasharray': '6'})

    ax.patch.set_facecolor('white')
    ax.patch.set_alpha(0.5)


    plt.xlabel('Wavelength (nm)', fontsize=16)
    plt.ylabel('Relative intensity (%)', fontsize=16)
    #print(json.dumps({'schart':mpld3.fig_to_dict(fig)}))
    return mpld3.fig_to_html(fig,no_extras=True)
    #TODO: return json.dumps(mpld3.fig_to_dict(fig)). It is most likely due to numpy which is not JSON supported, but where it the np???

    #mpld3.show()
