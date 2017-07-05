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
import itertools, time

from analytics.plot_bestfit import plot_data
from analytics.matlibplot_bestfit import matplot_data
from analytics.spectral_overlapper_optimized import fluorochrome_analyzed,auc_overlaps_fun
# Using base 300 index


"""
NUMPY array matrix

wl | Ex | Em


"""






class Overlap:
    def __init__(self):
        self.overlap = []

    def append_auc(self,val):
        self.overlap.appendO(val)


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


def get_spectra(i):
    #make class
    #get_spectra(spectra, i)
    pass

def spectral_overlapper(r,n,colors,lasers,c = 0.1):


    #start = time.time()

    # Connect to database
    db = dataDB()



    # Check whether the specific combination of lasers and colors has been evaluated before
    pre_data_check = db.check_basic_comb_log(n,lasers,colors)

    # If the combination has been evaluated before then simply plot that result
    if pre_data_check != None:

        return plot_data(pre_data_check, lasers,pre_data = True),matplot_data(pre_data_check, lasers,pre_data = True)
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
                m_ii =spectra[ii][list(spectra[ii].keys())[0]]

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

        db.add_basic_comb_log(n, lasers, colors, [item for i, item in enumerate(spectra) if i in min_list])
        plt_data = [item for i, item in enumerate(spectra) if i in min_list]
        return plot_data(plt_data,lasers),matplot_data(plt_data, lasers)

#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
#lasers = [355,405,488,561,640]
#start = time.time()
#spectral_overlapper(0,5,1,lasers)
#print("Total time")
#print(time.time()-start)