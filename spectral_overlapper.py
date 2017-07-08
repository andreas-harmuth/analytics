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
        colors = [name for name in json.loads(pre_data_check[0])]
        fluorochromes_all = db.fetch_fluorchromes_data(colors)
        fc_list = []
        for fc in fluorochromes_all:
            fc_list.append(fluorochrome_analyzed(fc,fluorochromes_all[fc],'clone',lasers))
        download_list = [obj.download_return() for obj in fc_list]
        return plot_data(pre_data_check, lasers,pre_data = True),matplot_data(pre_data_check, lasers,pre_data = True),\
               spillover_table(list(range(len(fc_list))), fc_list),download_list
        pass

    # If it haven't been evaluate then evaluate it
    else:
        f_counter = 0
        f_sub = [] # Create the sub data as list
        peak_wl = []  # Create the sub array for peak wavelengths
        test_list = [] # For debugging



        """
        ********************************************************
        *                                                      *
        *                   EMISSION RECALC                    *
        *                                                      *
        ********************************************************
        """

        # In this code the db side have taken care of setting emissions < 0 <- 0
        fluorochromes_all = db.fetch_fluorchromes_data(colors)


        # TODO:(LARS) Optimize by assuming index = i+300?
        # Compared to R we can just access the values directly from a for loop
        for fc_i,fc in enumerate(fluorochromes_all):
            tmp_val = fluorochrome_analyzed(fc,fluorochromes_all[fc],'clone',lasers)
            if tmp_val.valid:
                test_list.append(tmp_val)
            else:
                print("{0} omitted. Relative emission intensity is below {1} %".format(tmp_val.name, c * 100))


            # As we only want to increment fc_i of valid data, we do this by setting a counter when the data is invalid
            fc_i -= f_counter # TODO: only have valid counter instead?


            l_max = [] # Init array

            for laser_wl in lasers:

                # Extra loop compared to R.. Not good.. Not good - again be optimize with comment above
                for wl_i in range(len(fluorochromes_all[fc][:,0])):
                    # TODO: Change this to base 300 index
                    if fluorochromes_all[fc][:,0][wl_i] == laser_wl:

                        l_max.append(fluorochromes_all[fc][:,1][wl_i])


            # Set l_max to the index of the biggest l_max
            l_max = l_max.index(max(l_max))
            #if fc == 'Alexa Fluor 488':
                #te = fluorochrome_analyzed(fc,fluorochromes_all[fc],'clone',lasers)
                #te.debug(fluorochromes_all[fc][:,2])
                #print(fc,fluorochromes_all[fc][:, 2])

            # if the relative emission is higher than the constant c then proceed
            if fluorochromes_all[fc][:, 1][lasers[l_max]-300]/100 >= c:

                #TODO:(2)(Lars) should this be cloned??
                f_sub.append({fc: np.copy(fluorochromes_all[fc])})

                # TODO:(LARS) Do we need all col, or just wv and product of em and ex?



                # TODO:(1) Fix this so all elements are multiplied with the excitation that corresponds to the max laser!!!

                f_sub[fc_i][fc][:,2] =np.multiply(f_sub[fc_i][fc][:,2],f_sub[fc_i][fc][:,1][lasers[l_max]-300])/100
                # Todo:(2). The (1) fix might solve the copy in q(2)

                #test_list.append((300+np.argmax(fluorochromes_all[fc],axis=0)[2],fc))


                peak_wl.append(300+np.argmax(fluorochromes_all[fc][:,2]))

            else:
                # If the relative emission is less than that of c then print it and increment the f_counter-
                f_counter +=1
                print('test')
                print("{0} omitted. Relative emission intensity is below {1} %".format(fc,c*100))
                pass

        ## Sort the list
        test_list.sort()




        peak_wl = [i[0] for i in sorted(enumerate(peak_wl), key=lambda x: x[1])]
        #print(peak_wl)
        #print(test_list)

        ## Optimize sort by key if this get's to big. Pair the data in set
        spectra = [f_sub[i] for i in peak_wl]



        #print(spectra)
        """
            ********************************************************
            *                                                      *
            *                        OVERLAP                       *
            *                                                      *
            ********************************************************
            """

        auc_spectra = []

        # for index ind sepectra


        print("-" * 30)
        for i,obj in zip(range(len(spectra)),test_list):
            # Get the current name of the fluorochrome
            current_fc = list(spectra[i].keys())[0]

            auc_spectra.append(np.sum(spectra[i][current_fc][:, 2]))



            #print(current_fc,np.sum(spectra[i][current_fc][:, 2]))
            #print(obj.name,obj.total_area)



        ################ AUC OVERLAPS (Loss) ######################
        auc_overlaps = None # A way to know when it has been initialized

        # TODO: Optimize if time > big
        for i in range(len(spectra)):
            row = [] # Value placeholder

            # Init the data (so it is easier to access)
            m_i = spectra[i][list(spectra[i].keys())[0]]

            for ii in range(len(spectra)):

                # Init the data (so it is easier to access)
                m_ii = spectra[ii][list(spectra[ii].keys())[0]]

                wl_ol = [] # Init list containing wave lengths where i and ii overlap
                for j in range(len(m_i[:,0])):
                    ## Assume all wl present
                    if m_i[:,2][j]> 0 and m_ii[:,2][j]> 0:
                        wl_ol.append(j+300)

                if len(wl_ol) == 0:
                    #wl_ol = 0
                    wl_ol_vec = []
                else:
                    wl_ol = [min(wl_ol)-1] + wl_ol + [max(wl_ol)+1]
                    # TODO:(3) Assume base 300 in above??. What happens when wl_ol = 0?
                    wl_ol_vec = [wl - 300 for wl in wl_ol]

                loss_i = m_i[:,2][wl_ol_vec]-m_ii[:,2][wl_ol_vec]
                ## sum of of the emission where the loss is less or equal to 0
                loss_i = np.sum([ele for ele,loss in zip(m_i[:,2][wl_ol_vec],loss_i) if loss <= 0])

                loss_i = loss_i/auc_spectra[i]

                loss_ii = m_ii[:, 2][wl_ol_vec] - m_i[:, 2][wl_ol_vec]
                ## sum of of the emission where the loss is less or equal to 0
                loss_ii = np.sum([ele for ele, loss in zip(m_ii[:, 2][wl_ol_vec], loss_ii) if loss <= 0])

                loss_ii = loss_ii / auc_spectra[ii ]

                row.append(round(loss_i+loss_ii,8))


            if auc_overlaps is not None:
                # If the auc_overlaps have been made an array then add the row to it
                auc_overlaps = np.vstack((auc_overlaps , np.array(row)))

            else:
                # If the auc_overlaps is equal to None it means it has not yet been initialized. Therefore it is inited as an array
                auc_overlaps = np.array(row)
        auc_overlaps = auc_overlaps_fun(test_list)



        comb = [1,2,3,4,5]
        for i in comb:
            for j in comb:
                print(auc_overlaps[i, j])
        print('*'*20)
        for i in comb:
            print(auc_overlaps[i])

        return
        start = time.time()
        comb = itertools.combinations(range(auc_overlaps.shape[0]), n)
        print('Combinations')
        print(time.time() - start)

        if n <= 6:
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
        plt_data_obj = [test_list[i] for i in min_list]
        db.add_basic_comb_log(n, lasers, colors, [item for i, item in enumerate(spectra) if i in min_list])
        plt_data = [item for i, item in enumerate(spectra) if i in min_list]

        return plot_data(plt_data,lasers),matplot_data(plt_data, lasers),spillover_table(min_list,plt_data_obj)



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
    #print(auc_overlaps)

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
    #print(list(min_list))
    #print(fc_list)
    plt_data = [fc_list[i] for i in min_list]

    return advanced_plot_data(plt_data, lasers),spillover_table(min_list,plt_data)





#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
#lasers = [355,405,488,561,640]
#start = time.time()
#spectral_overlapper(0,5,1,lasers)
#print("Total time")
#print(time.time()-start)