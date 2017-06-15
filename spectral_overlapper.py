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

# Using base 300 index


"""
NUMPY array matrix

wl | Ex | Em


"""

def get_spectra(i):
    #make class
    #get_spectra(spectra, i)
    pass

def spectral_overlapper(r,n,colors,lasers,c = 0.1):
    db = dataDB()
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
    fluorochromes_all = db.fetch_fluorchromes_data_test(colors)



    # TODO:(LARS) Optimize by assuming index = i+300?

    # Compared to R we can just access the values directly from a for loop

    for fc_i,fc in enumerate(fluorochromes_all):

        fc_i -= f_counter
        l_max = [] # Init array

        for laser_wl in lasers:

            # Extra loop compared to R.. Not good.. Not good - again be optimize with comment above
            for wl_i in range(len(fluorochromes_all[fc][:,0])):
                # Change this to base 300 index
                if fluorochromes_all[fc][:,0][wl_i] == laser_wl:

                    l_max.append(fluorochromes_all[fc][:,1][wl_i])


        l_max = l_max.index(max(l_max))

        # Check

        if fluorochromes_all[fc][:, 1][lasers[l_max]-300]/100 >= c:

            #TODO:(2)(Lars) should this be cloned??
            f_sub.append({fc: np.copy(fluorochromes_all[fc])})

            # TODO:(LARS) Do we need all col, or just wv and product of em and ex?



            # TODO:(1) Fix this so all elements are multiplied with the excitation that corresponds to the max laser!!!
            f_sub[fc_i][fc][:,2] = np.multiply(f_sub[fc_i][fc][:,2],f_sub[fc_i][fc][:,1][lasers[l_max]-300])/100
            # Todo:(2). The (1) fix might solve the copy in q(2)

            test_list.append((300+np.argmax(fluorochromes_all[fc],axis=0)[2],fc))


            ## append the value (with the 0
            #print(np.argmax(fluorochromes_all[fc][:,2]))
            peak_wl.append(300+np.argmax(fluorochromes_all[fc][:,2]))

        else:
            f_counter +=1
            print("{0} omitted. Relative emission intensity is below {1} %".format(fc,c*100))
            pass


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

    for i in range(len(spectra)):
        # Get the current name of the fluorochrome
        current_fc = list(spectra[i].keys())[0]

        auc_spectra.append(np.sum(spectra[i][current_fc][:, 2]))

        #print(np.sum(spectra[i][current_fc], axis=0)[1])

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
                wl_ol = 0
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


        if auc_overlaps != None:
            # If the auc_overlaps have been made an array then add the row to it
            auc_overlaps = np.vstack((auc_overlaps , np.array(row)))

        else:
            # If the auc_overlaps is equal to None it means it has not yet been initialized. Therefore it is inited as an array
            auc_overlaps = np.array(row)



#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
lasers = [355,405,488,561,640]
spectral_overlapper(0,6,1,lasers)