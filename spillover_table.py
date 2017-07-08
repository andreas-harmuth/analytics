#import numpy as np

def spillover_table(min_list, fc_list_sorted):
    spillover_matrix = []


    header_row = ['']

    for main_color in fc_list_sorted:
        header_row.append(main_color.name)
        mc = main_color.M[:,2]
        loss_row = [main_color.name]
        for sub_color in fc_list_sorted:
            if sub_color.name == main_color.name:
                cell = 100
            else:
                loss = 0
                sc = sub_color.M[:, 2]
                for i in range(len(mc)):
                    if mc[i] > 0 and sc[i] > 0:
                        loss += min(mc[i],sc[i])

                cell = round(100*loss/sub_color.total_area,3)
            loss_row.append(cell)
        spillover_matrix.append(loss_row)

    return {'table':spillover_matrix,'header':header_row}
