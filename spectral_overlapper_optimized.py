## Assumptions
# Index 300

import numpy as np
from analytics.wl_to_rbg import wavelength_to_rgb


class fluorochrome_analyzed:
    __slots__ = ['c', 'name', 'M','type','l_max_laser','valid','peak_wl','total_area','marker']

    def __init__(self, name, matrix, type, lasers):
        self.marker = ""
        self.c = 0.1
        self.name = name
        self.M = np.copy(matrix)
        self.type = type


        # Find max laser
        max_list = [self.M[:, 1][laser_wl - 300] for laser_wl in lasers]

        self.l_max_laser = lasers[max_list.index(max(max_list))]

        self.valid = self.M[:, 1][self.l_max_laser - 300] >= self.c




        self.M[:, 2] = np.multiply(self.M[:, 2], self.M[:, 1][self.l_max_laser - 300]) / 100
        self.peak_wl = 300 + np.argmax(self.M[:, 2])
        
        self.total_area = np.sum(self.M[:, 2])# The total area. Is used to calculate relative %

        self.valid = self.M[:, 1][self.l_max_laser-300]/100 >= self.c

    # This let's us sort after max peak wavelength
    def __lt__(self, other):
        return self.peak_wl < other.peak_wl


    def debug(self):
        print(self.__dict__)

    def download_return(self):
        return {'rgb'       : wavelength_to_rgb(self.peak_wl),
                'name'      : self.name,
                'wavelength': [a for a in self.M[:, 0]],
                'excitation': [a for a in self.M[:, 1]],
                'emission'  : [a for a in self.M[:,2]]
                }


def auc_overlaps_fun(spectra):
    auc_overlaps = None

    for i in range(len(spectra)):

        row = []  # Value placeholder

        # Init the data (so it is easier to access)
        m_i = spectra[i].M

        for ii in range(len(spectra)):

            # Init the data (so it is easier to access)
            m_ii = spectra[ii].M

            wl_ol = []  # Init list containing wave lengths where i and ii overlap
            for j in range(len(m_i[:, 0])):
                ## Assume all wl present
                if m_i[:, 2][j] > 0 and m_ii[:, 2][j] > 0:
                    wl_ol.append(j + 300)

            if len(wl_ol) == 0:
                # wl_ol = 0
                wl_ol_vec = []
            else:
                wl_ol = [min(wl_ol) - 1] + wl_ol + [max(wl_ol) + 1]
                # TODO:(3) Assume base 300 in above??. What happens when wl_ol = 0?
                wl_ol_vec = [wl - 300 for wl in wl_ol]

            loss_i = m_i[:, 2][wl_ol_vec] - m_ii[:, 2][wl_ol_vec]
            ## sum of of the emission where the loss is less or equal to 0
            loss_i = np.sum([ele for ele, loss in zip(m_i[:, 2][wl_ol_vec], loss_i) if loss <= 0])

            loss_i = loss_i / spectra[i].total_area

            loss_ii = m_ii[:, 2][wl_ol_vec] - m_i[:, 2][wl_ol_vec]
            ## sum of of the emission where the loss is less or equal to 0
            loss_ii = np.sum([ele for ele, loss in zip(m_ii[:, 2][wl_ol_vec], loss_ii) if loss <= 0])

            loss_ii = loss_ii / spectra[ii].total_area

            row.append(loss_i + loss_ii)

        if auc_overlaps is not None:
            # If the auc_overlaps have been made an array then add the row to it
            auc_overlaps = np.vstack((auc_overlaps, np.array(row)))

        else:
            # If the auc_overlaps is equal to None it means it has not yet been initialized. Therefore it is inited as an array
            auc_overlaps = np.array(row)

    return auc_overlaps


def auc_spill_fun(fc_list):
    auc_overlaps = None


    for main_color in fc_list:

        mc = main_color.M[:, 2]
        loss_row = []

        for sub_color in fc_list:
            if sub_color.name == main_color.name:
                cell = 100
            else:
                loss = 0
                sc = sub_color.M[:, 2]
                for i in range(len(mc)):
                    if mc[i] > 0 and sc[i] > 0:
                        loss += min(mc[i], sc[i])

                cell = round(loss / sub_color.total_area)

            loss_row.append(cell)

        if auc_overlaps is not None:
            # If the auc_overlaps have been made an array then add the row to it
            auc_overlaps = np.vstack((auc_overlaps, np.array(loss_row)))

        else:
            # If the auc_overlaps is equal to None it means it has not yet been initialized. Therefore it is inited as an array
            auc_overlaps = np.array(loss_row)

    return auc_overlaps





