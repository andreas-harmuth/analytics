import json
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(color_codes=True)

# Load the json file downloaded from the webpage
with open('fluro_select_data.json') as data_file:

    # The text settings
    font = {'family': 'monospace',
            'weight': 'black',
            'color': '#242424',
            'size': 10,
            'horizontalalignment': 'center',
            'verticalalignment': 'center'
            }

    # Load it as a dictionary
    data = json.load(data_file)
    plot_data = data['color_data']
    lasers = data['lasers']


    x = plot_data[0]['wavelength']
    # Init the main graph

    # Init the figure. The size is given in inches
    fig = plt.figure(figsize=(10, 6))

    # Create the sub plot, which will be operated on
    ax = fig.add_subplot(111)


    # Main loop of the data
    for fc in plot_data:
        name = fc['name']


        color = tuple([val/255 for val in list(fc['rgb'])])
        ax.fill_between(fc['wavelength'], [val if val > 0 else 0 for val in fc['emission']],
                        color=color,
                        alpha=.5)

        ax.plot(fc['wavelength'], [val if val > 0 else 0 for val in fc['excitation']], ':', linewidth=0.8,
                color=color,
                alpha=.7)



        ax.text((fc['emission'].index(max(fc['emission']))+300), 30, name, fontdict=font, rotation=90)



    # Add the lasers
    for laser in lasers:


        ax.plot([laser, laser], [0, 100], linestyle='--', color='grey', linewidth=0.8)
        ax.text(laser, 95, str(laser) + " nm", fontdict=font, rotation=45)

    # Set the facecolor to white
    ax.patch.set_facecolor('white')
    ax.patch.set_alpha(0.5)

    plt.xlabel('Wavelength (nm)', fontsize=16)
    plt.ylabel('Relative intensity (%)', fontsize=16)

    # Save the figure - this might take some time
    try:
        plt.savefig('FlouroSelect.pdf', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
        print("The plot have been saved as basic_python_example.pdf")

    except:
        print("Something went wrong! Try again.")