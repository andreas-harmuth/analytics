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

def spectral_overlapper(r,colors,lasers,c = 0.1):
    db = dataDB()
    f_counter = 0
    f_sub = [] # Create the sub data as list
    peak_wl = []  # Create the sub array for peak wavelengths
    test_list = [] # For debugging
    ################ EMISSION RECALC ##################

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
                    #print(laser_wl)
                    l_max.append(fluorochromes_all[fc][:,1][wl_i])
                    #l_max.append(wl_i)
        #print(l_max)
        l_max = l_max.index(max(l_max))
        #print(l_max)

        # Check
        #print(print(l_max))
        if fluorochromes_all[fc][:, 1][lasers[l_max]-300]/100 >= c:

            f_sub.append({fc: fluorochromes_all[fc]})

            # TODO:(LARS) Do we need all col, or just wv and product of em and ex?
            #a,b = f_sub[fc_i][fc][:,1],f_sub[fc_i][fc][:,2]

            f_sub[fc_i][fc][:,1] = np.multiply(f_sub[fc_i][fc][:,1],f_sub[fc_i][fc][:,2])/100

            print(fc)
            print(300+np.argmax(fluorochromes_all[fc][:,2]))
            test_list.append((300+np.argmax(fluorochromes_all[fc][:,2]),fc))
            ## Todo: Wrong values??
            print(fluorochromes_all[fc][np.argmax(fluorochromes_all[fc][:, 2]), 2])
            ## append the value (with the 0
            peak_wl.append(300+np.argmax(fluorochromes_all[fc][:,2]))

        else:
            f_counter +=1
            print("{0} omitted. Relative emission intensity is below {1} %".format(fc,c*100))
            pass


    peak_wl = [i[0] for i in sorted(enumerate(peak_wl), key=lambda x: x[1])]



    ## Optimize sort by key if this get's to big. Pair the data in set
    f_sub_order = [f_sub[i] for i in peak_wl]

    # expected output:
    expect_val = ["Alexa Fluor 405", "Alexa Fluor 350", "eFluor 450", "7-hydroxy-4-methylcoumarin", "Pacific Blue", "1,8-ANS", "eFluor 506", "FITC", "Alexa Fluor 488", "Acridine orange", "Alexa Fluor 430", "Alexa Fluor 514", "Alexa Fluor 532", "Alexa Fluor 555", "eFluor 570", "Alexa Fluor 546", "PE", "alamarBlue", "4-Di-10-ASP", "Alexa Fluor 568", "PE-eFluor 610", "eFluor 615", "PE-Texas Red", "Alexa Fluor 594", "Alexa Fluor 610", "YOYO-3", "7-AAD (7-aminoactinomycin D)", "Alexa Fluor 635", "Alexa Fluor 633", "APC", "PE-Cy5", "eFluor 660", "Alexa Fluor 647", "PE-Cy5.5", "PerCP", "PerCP-Cy5.5", "Alexa Fluor 660", "PerCP-eFluor 710", "eFluor 710", "Alexa Fluor 700", "Alexa Fluor 750", "PE-Cy7", "APC-Alexa Fluor 750", "APC-eFluor 780"]


    #print(test_list)
    #print(sorted(test_list))

    for fo, f in zip(f_sub_order, expect_val):
        print(fo.keys(), f)

    print("*"*50)
    for fo, f in zip(sorted(test_list), expect_val):
        print(fo[1], f)

#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # R
#0 0 0 1 1 1 1 1 2 2 2 2 2 2 2 2 2 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 4 4 4 4 4 4 4 4 4 4 4 4 # Python
lasers = [355,405,488,561,640]
spectral_overlapper(0,1,lasers)