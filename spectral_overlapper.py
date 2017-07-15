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




from analytics.dataDB import dataDB
import numpy as np
import itertools, time,json
from multiprocessing import Process, Queue


from analytics.plot_bestfit import plot_data, advanced_plot_data
from analytics.matlibplot_bestfit import matplot_data
from analytics.spillover_table import spillover_table
from analytics.spectral_overlapper_optimized import fluorochrome_analyzed,auc_overlaps_fun
# Using base 300 index


"""
NUMPY array matrix

wl | Ex | Em


"""


def choose(n, k):
    """
    A fast way to calculate binomial coefficients by Andrew Dalke (contrib).
    """
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in range(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0


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


def process_search(auc_overlaps, comb,q,name):

    current_min = 10000  # Theoretical max?
    min_list = []

    for i, comb_ele in enumerate(comb):

        val = twist_sum(auc_overlaps, list(comb_ele), current_min)
        if val < current_min:
            current_min = val
            min_list = comb_ele

    q.put([current_min,min_list])

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


        arr = np.append(arr, np.array([
            [int(kk in li) for li in mark_list]
        ]), axis=0)

    if sum((np.sum(arr, axis=0)>1)*1) >= n:
        return counter

    else:
        return c_min





def spectral_overlapper(n,colors,lasers,c = 0.2,time_out = 100):



    # Connect to database
    db = dataDB()



    # Check whether the specific combination of lasers and colors has been evaluated before
    pre_data_check = db.extended_check_basic_comb_log(n,lasers,colors)


    # If the combination has been evaluated before then simply plot that result
    if pre_data_check != None:

        # Find all the fluorochromes data
        fluorochromes_all = db.fetch_fluorchromes_data(json.loads(pre_data_check))

        # Create a list of fc objects
        fc_list = [fluorochrome_analyzed(fc,fluorochromes_all[fc],'clone',lasers) for fc in fluorochromes_all]

        # Create the list for download
        download_list = [obj.download_return() for obj in fc_list]

        # Return everything
        return advanced_plot_data(fc_list , lasers,pre_data = True),matplot_data(fc_list , lasers,pre_data = True),\
               spillover_table(list(range(len(fc_list))), fc_list),download_list
        pass

    # If it haven't been evaluate then evaluate it
    else:


        # Init the list
        fc_list = []


        # In this code the db side have taken care of setting emissions < 0 <- 0
        fluorochromes_all = db.fetch_fluorchromes_data(colors)


        # If the fluorochrome is valid at the given laser then add it to the list
        for fc in fluorochromes_all:
            fc_obj = fluorochrome_analyzed(fc, fluorochromes_all[fc], 'clone', lasers)

            if fc_obj.valid:
                fc_list.append(fc_obj)
            else:
                # Todo: return list?
                # Tell if has been omitted
                print("{0} omitted. Relative emission intensity is below {1} %".format(fc_obj.name, c * 100))

        ## Sort the list
        fc_list.sort()


        # Calculate the overlapc
        auc_overlaps = auc_overlaps_fun(fc_list)

        # Get number of rows
        r = auc_overlaps.shape[0]

        # Get the expected size of the generator
        size = choose(r, n)
        start = time.time()


        # Running 4 process
        proc = 4
        splitter = size // proc # Diving the size by proc and return the integer value
        rest_split = size % proc # get the remainder
        comb = itertools.combinations(range(r), n) # Create the generator


        main_list = [] # Create an empty list to append to
        for i in range(proc):
            if i == proc - 1:
                itertools.islice(comb, splitter * i, splitter * (i + 1) + rest_split)

            main_list.append(itertools.islice(comb, splitter * i, splitter * (i + 1)))

        # main_list [itertools.islice(comb, splitter * i, splitter * (i + 1) + rest_split) if i != proc - 1 else
        #  main_list.append(itertools.islice(comb, splitter * i, splitter * (i + 1))) for i in range(proc)]


        q = Queue()
        for i, sub_list in enumerate(main_list):

            p = Process(target=process_search, args=(auc_overlaps,sub_list, q, "sub {0}".format(i)))
            p.Daemon = True
            p.start()

        for tmp in main_list:
            p.join()

        res = []

        ## Todo; check res length instead, or add timeout
        run_time = time.time()

        while True:
            res.append(q.get())
            if len(res) == 4:
                break
            if run_time+time_out >= time.time():
                # Todo: what to return?
                return
        min_list = min(res, key = lambda t: t[0])[1]

        print('Find best')
        print(time.time()-start)




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
    r = auc_overlaps.shape[0]
    comb = itertools.combinations(range(r), n)

    print('Combinations')
    print(time.time() - start)






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




    plt_data = [fc_list[i] for i in min_list]

    return advanced_plot_data(plt_data, lasers),spillover_table(min_list,plt_data)





#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
#lasers = [355,405,488,561,640]
#start = time.time()
#spectral_overlapper(0,5,1,lasers)
#print("Total time")
#print(time.time()-start)