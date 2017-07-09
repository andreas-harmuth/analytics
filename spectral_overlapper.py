#################################################
#                                               #
#        A pythonic interpretation of:          #
#                                               #
#               Compensator v1.0                #
#                   05/05-2017                  #
#                 Developed by:                 #
#  Lars Ronn Olsen and Mike Bogetofte Barnkob   #
#                                               #
#     Base on the interface and db of /flow     #
#                                               #
#################################################


#TODO:(BUG) 355,405,488,561,642; graph not right; check R

from analytics.dataDB import dataDB
import numpy as np
import itertools, time,json

from analytics.plot_bestfit import plot_data, advanced_plot_data
from analytics.matlibplot_bestfit import matplot_data
from analytics.spillover_table import spillover_table
from analytics.spectral_overlapper_optimized import fluorochrome_analyzed,auc_overlaps_fun
# Using base 300 index


"""
NUMPY array matrix

wl | Ex | Em


"""





# TODO: class all these functions
def twist_sum(auc_overlaps,comb,c_min):

    # TODO: implement the the search part as well
    counter = 0
    n = len(comb)

    for j in range(n-1):
        for i in range(j+1,n):


            counter += (auc_overlaps[comb[i], comb[j]])
            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                #print(j)
                return counter

    return counter




# TODO: class all these functions
def adv_twist_sum(auc_overlaps,comb,c_min,mark_list):

    # TODO: implement the the search part as well
    counter = 0
    n       = len(comb)
    n_m     = len(mark_list)  # Rows in check matrix


    for j in range(n-1):
        for i in range(j+1,n):


            counter += (auc_overlaps[comb[i], comb[j]])
            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                #print(j)
                return counter


    # TODO: Is it needed to

    arr = np.empty((0, n_m), int)

    ## Check row matrix. The columns correspond to list of colors in markers and the rows the numbers in the combination.
    ## If the number of col having a sum over 1 is more than n, then it's valid.
    for kk in comb:

        """
        row = []
        for li in mark_list:

            row.append(int(kk in li))
        arr = np.append(arr, np.array([row]), axis=0)
        """
        arr = np.append(arr, np.array([
            [int(kk in li) for li in mark_list]
        ]), axis=0)

    if sum((np.sum(arr, axis=0)>1)*1) >= n:
        return counter

    else:
        return c_min



def rel_twist_sum(auc_overlaps,spectra,comb,c_min):

    # TODO: implement the the search part as well
    counter = 0
    n = len(comb)

    for j in range(n-1):
        for i in range(j+1,n):

            counter += (auc_overlaps[comb[i], comb[j]])/(spectra[i].total_area)+(auc_overlaps[comb[i], comb[j]])/(spectra[j].total_area)

            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                #print(j)
                return counter

    return counter





def spectral_overlapper(n,colors,lasers,c = 0.1):


    #start = time.time()

    # Connect to database
    db = dataDB()



    # Check whether the specific combination of lasers and colors has been evaluated before
    pre_data_check = db.check_basic_comb_log(n,lasers,colors)

    # If the combination has been evaluated before then simply plot that result
    if pre_data_check != None:

        fluorochromes_all = db.fetch_fluorchromes_data(json.loads(pre_data_check[0]))

        fc_list = []
        for fc in fluorochromes_all:
            fc_list.append(fluorochrome_analyzed(fc,fluorochromes_all[fc],'clone',lasers))

        download_list = [obj.download_return() for obj in fc_list]
        return advanced_plot_data(fc_list , lasers,pre_data = True),matplot_data(fc_list , lasers,pre_data = True),\
               spillover_table(list(range(len(fc_list))), fc_list),download_list
        pass

    # If it haven't been evaluate then evaluate it
    else:



        test_list = [] # For debugging

        fc_list = []


        # In this code the db side have taken care of setting emissions < 0 <- 0
        fluorochromes_all = db.fetch_fluorchromes_data(colors)

        for fc in fluorochromes_all:
            fc_obj = fluorochrome_analyzed(fc, fluorochromes_all[fc], 'clone', lasers)
            if fc_obj.valid:
                fc_list.append(fc_obj)
            else:
                print("{0} omitted. Relative emission intensity is below {1} %".format(fc_obj.name, c * 100))

        ## Sort the list
        fc_list.sort()

        auc_overlaps = auc_overlaps_fun(fc_list)







        start = time.time()
        comb = itertools.combinations(range(auc_overlaps.shape[0]), n)
        print('Combinations')
        print(time.time() - start)

        if n <= 9:
            current_min = 100 # Theoretical max?
            min_list = []
            start = time.time()
            for i,comb_ele in enumerate(comb):

                val = twist_sum(auc_overlaps,list(comb_ele),current_min)
                if val < current_min:
                    current_min = val
                    min_list = comb_ele

            print('Find best')
            print(time.time()-start)

        else:
            print("No algorithm have been developed to handle this n size yet")


        plt_data = [fc_list[i] for i in min_list]



        db.add_basic_comb_log(n, lasers, colors, plt_data)

        # Create the list of downloadable material
        download_list = [obj.download_return() for obj in fc_list]
        return advanced_plot_data(plt_data, lasers),matplot_data(plt_data, lasers),spillover_table(min_list, plt_data),\
               download_list



def spectral_overlapper_advanced(n, markers, lasers, c=0.1):



    # Find all colors used
    colors = list(set([color for marker in markers.values() for color in marker['color']]))


    #all_colors = [color for color in marker['color'] for marker in markers.values()]
    db = dataDB()
    fluorochromes_all = db.fetch_fluorchromes_data(colors)


    fc_list = []
    fc_list_omitted = []
    for fc_i, fc in enumerate(fluorochromes_all):
        fc_obj = fluorochrome_analyzed(fc, fluorochromes_all[fc], 'clone', lasers)
        if fc_obj.valid:
            fc_list.append(fc_obj)
        else:
            fc_list_omitted.append(fc_obj.name)
            print("{0} omitted. Relative emission intensity is below {1} %".format(fc_obj.name, c * 100))


    # Sort list by peak
    fc_list.sort()
    fc_list_by_name = [obj.name for obj in fc_list]

    fc_list_by_index = [[fc_list_by_name.index(co) for co in marker['color'] if co not in fc_list_omitted] for marker in markers.values()]

    # Find the auc_overlaps
    auc_overlaps = auc_overlaps_fun(fc_list)


    start = time.time()
    comb = itertools.combinations(range(auc_overlaps.shape[0]), n)
    print('Combinations')
    print(time.time() - start)

    #def twist_sum(auc_overlaps, comb, c_min):


    if n <= 6:
        current_min = 100  # Theoretical max?
        min_list = []
        start = time.time()
        for i, comb_ele in enumerate(comb):

            val = adv_twist_sum(auc_overlaps, list(comb_ele), current_min,fc_list_by_index)

            if val < current_min:

                current_min = val
                min_list = comb_ele

        print('Find best')
        print(time.time() - start)

    else:
        print("No algorithm have been developed to handle this n size yet")

    plt_data = [fc_list[i] for i in min_list]

    return advanced_plot_data(plt_data, lasers),spillover_table(min_list,plt_data)





#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
#lasers = [355,405,488,561,640]
#start = time.time()
#spectral_overlapper(0,5,1,lasers)
#print("Total time")
#print(time.time()-start)