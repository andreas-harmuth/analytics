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
from analytics.spectral_overlapper_optimized import fluorochrome_analyzed,auc_overlaps_fun,auc_spill_fun
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
    #debub_val = 1.1
    # TODO: implement the the search part as well
    counter = 0

    n = len(comb)

    for j in range(n-1):
        for i in range(j+1,n):

            #if auc_overlaps[comb[i], comb[j]] > debub_val:
            #    print(auc_overlaps[comb[i], comb[j]])
            #    return 10000

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



################## ADVANCED #################



def matrix_validator(arr, n, m_comb):
    # Looks for any diagonal. As we are using markers, we want a diagonal where the trace = n
    for i in m_comb:

        if sum(arr[:, i].diagonal() > 0) >= n:
            return True

    return False


def adv_twist_sum(auc_overlaps,comb,c_min,mark_list):

    # TODO: implement the the search part as well
    counter = 0
    n       = len(comb)

    m_comb = itertools.permutations(range(n))
    # todo: n_m = n right?? Check this

    for j in range(n-1):
        for i in range(j+1,n):


            counter += (auc_overlaps[comb[i], comb[j]])
            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                #print(j)
                return counter


    # TODO: Is it needed to

    arr = np.empty((0, n), int)

    ## Check row matrix. The columns correspond to list of colors in markers and the rows the numbers in the combination.
    ## If the number of col having a sum over 0 is more than n, then it's valid.
    for kk in comb:


        arr = np.append(arr, np.array([
            [int(kk in li) for li in mark_list]
        ]), axis=0)

    if matrix_validator(arr, n, m_comb):
        return counter

    else:
        return c_min





def spectral_overlapper(n,colors,lasers,c = 0.2,time_out = 100):
    start = time.time()
    pl_lasers = lasers

    # Connect to database
    db = dataDB()


    """Developer commment:
    
    The reason we init the list here, is so we can check what lasers are used. We can then sort the lasers not in use,
    and thereby get a higher chance of having the result being in the db already! 
    """


    # In this code the db side have taken care of setting emissions < 0 <- 0
    fluorochromes_all = db.fetch_fluorchromes_data(colors)

    # Init the list
    fc_list = []

    # If the fluorochrome is valid at the given laser then add it to the list
    for fc in fluorochromes_all:
        fc_obj = fluorochrome_analyzed(fc, fluorochromes_all[fc], 'clone', lasers)

        if fc_obj.valid:
            fc_list.append(fc_obj)
        else:
            # Todo: return list?
            # Tell if has been omitted
            print("{0} omitted. Relative emission intensity is below {1} %".format(fc_obj.name, c * 100))


    lasers = sorted(list(set([fc.l_max_laser for fc in fc_list])))

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
        return advanced_plot_data(fc_list , pl_lasers,pre_data = True),matplot_data(fc_list , pl_lasers,pre_data = True),\
               spillover_table(list(range(len(fc_list))), fc_list),download_list
        pass

    # If it haven't been evaluate then evaluate it
    else:


        ## Sort the list of fluorochromes
        fc_list.sort()


        # Calculate the overlapc
        auc_overlaps = auc_overlaps_fun(fc_list)#auc_overlaps_fun(fc_list)

        # Get number of rows
        r = auc_overlaps.shape[0]

        # Get the expected size of the generator
        size = choose(r, n)




        proc = 4 # Running 4 process
        splitter = size // proc # Diving the size by proc and return the integer value
        rest_split = size % proc # get the remainder

        comb = itertools.combinations(range(r), n) # Create the generator


        #main_list = [] # Create an empty list to append to

        # Chunkify the list
        """
        for i in range(proc):
            if i == proc - 1:
                # If it is the last "list"-element, then add the remainder to the index splice
                itertools.islice(comb, splitter * i, splitter * (i + 1) + rest_split)

            # Add the chunk
            main_list.append(itertools.islice(comb, splitter * i, splitter * (i + 1)))
        """

        # Same as above
        main_list =  [itertools.islice(comb, splitter * i, splitter * (i + 1) + rest_split) if i == proc - 1 else
                      itertools.islice(comb, splitter * i, splitter * (i + 1)) for i in range(proc)]

        # Create the queue
        q = Queue()

        # Init the multiprocessing
        for i, sub_list in enumerate(main_list):

            # Call the function
            p = Process(target=process_search, args=(auc_overlaps,sub_list, q, "sub {0}".format(i)))
            # Run in the background
            p.Daemon = True
            p.start()

        # "Connect" the queues
        for tmp in main_list:
            p.join()

        # Init a list containing the answers
        res = []

        ## Todo; check res length instead, or add timeout
        run_time = time.time()

        while True:
            # Append a queue to the result list
            res.append(q.get())

            # If all the processes are done
            if len(res) == proc:
                break

            # If it is running to slow then break it
            if run_time+time_out <= time.time():
                print(time_out)
                # Todo: what to return?
                return

        # Find the combination that is smallest - each process returns the smallest list of the chunck it evaluated
        min_list = min(res, key = lambda t: t[0])[1]



        db.speed_test(time.time()-run_time,size,'macBookPro')



        # Find the color object corresponding to the list
        plt_data = [fc_list[i] for i in min_list]


        # Add the combination and result to the database
        db.add_basic_comb_log(n, lasers, colors, plt_data)

        # Create the list of downloadable material
        download_list = [obj.download_return() for obj in fc_list]

        # Return everything
        return advanced_plot_data(plt_data, pl_lasers),matplot_data(plt_data, pl_lasers),spillover_table(min_list, plt_data),\
               download_list



def spectral_overlapper_advanced(n, extra_markers, markers, lasers, c=0.1):

    # Markers key is the id. We can just continue the id chain
    start_id = max([int(marker) for marker in markers])

    # Create the extra markers

    for i in range(n):

        markers[str(start_id+i+1)] = {'color': [color['name'] for color in extra_markers['color']]}

    n = len(markers)


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