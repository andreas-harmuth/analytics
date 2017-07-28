# auto_generate_data
#
# Auto generate the data for the combination database
#
# Todo-list
# 1. Return size, to find out how quick the program is; on found and not found
# 2. Optimize multiprocessing


from analytics.dataDB import dataDB
import itertools, time, json
from multiprocessing import Process, Queue
from analytics.spectral_overlapper_optimized import fluorochrome_analyzed, auc_overlaps_fun





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


def twist_sum(auc_overlaps, comb, c_min):
    counter = 0

    n = len(comb)

    for j in range(n - 1):
        for i in range(j + 1, n):

            # if auc_overlaps[comb[i], comb[j]] > debub_val:
            #    print(auc_overlaps[comb[i], comb[j]])
            #    return 10000

            counter += (auc_overlaps[comb[i], comb[j]])
            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                # print(j)
                return counter

    return counter


def process_search(auc_overlaps, comb, q, name):
    current_min = 10000  # Theoretical max?
    min_list = []

    for i, comb_ele in enumerate(comb):

        val = twist_sum(auc_overlaps, list(comb_ele), current_min)
        if val < current_min:
            current_min = val
            min_list = comb_ele

    q.put([current_min, min_list])









def speed_results(n,lasers,colors):




    time_out = 11000 # approx 3 hours
    run_time = time.time()




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

            # Tell if has been omitted
            #print("{0} omitted. Relative emission intensity is below {1} %".format(fc_obj.name, c * 100))
            pass

    lasers = sorted(list(set([fc.l_max_laser for fc in fc_list])))

    # Check whether the specific combination of lasers and colors has been evaluated before
    pre_data_check = db.extended_check_basic_comb_log(n, lasers, colors)

    # If the combination has been evaluated before then simply plot that result
    if pre_data_check != None:
        # Don't do anything
        return json.loads(pre_data_check),0


    # If it haven't been evaluate then evaluate it
    else:

        ## Sort the list of fluorochromes
        fc_list.sort()

        # Calculate the overlapc
        auc_overlaps = auc_overlaps_fun(fc_list)  # auc_overlaps_fun(fc_list)

        # Get number of rows
        r = auc_overlaps.shape[0]

        # Get the expected size of the generator
        size = choose(r, n)

        splitter = size // proc  # Diving the size by proc and return the integer value
        rest_split = size % proc  # get the remainder

        comb = itertools.combinations(range(r), n)  # Create the generator


        # Same as above
        main_list = [itertools.islice(comb, splitter * i, splitter * (i + 1) + rest_split) if i == proc - 1 else
                     itertools.islice(comb, splitter * i, splitter * (i + 1)) for i in range(proc)]

        # Create the queue
        q = Queue()

        # Init the multiprocessing
        for i, sub_list in enumerate(main_list):
            # Call the function
            p = Process(target=process_search, args=(auc_overlaps, sub_list, q, "sub {0}".format(i)))
            # Run in the background
            p.Daemon = True
            p.start()

        # "Connect" the queues
        for tmp in main_list:
            p.join()

        # Init a list containing the answers
        res = []



        while True:
            # Append a queue to the result list
            res.append(q.get())

            # If all the processes are done
            if len(res) == proc:
                break

            # If it is running to slow then break it
            if run_time + time_out <= time.time():
                print("time_out")
                # Todo: what to return?


        # Find the combination that is smallest - each process returns the smallest list of the chunck it evaluated
        min_list = min(res, key=lambda t: t[0])[1]


        # Add the combination and result to the database
        #print(n, lasers, colors, [fc_list[i] for i in min_list])
        db.add_basic_comb_log(n, lasers, colors, [fc_list[i] for i in min_list])
        return [fc_list[i].name for i in min_list],1

# Init the database
db = dataDB()

# From n
n_small = 5

# To n
n_big = 14

# Processes
proc = 8

# Lasers
lasers = [320, 405, 488, 561, 640]

# Levels
levels = 3

levels += 1

start = time.time()
counter = 0
if __name__ ==  '__main__':
    for n in range(n_small, n_big + 1):

        r = [[] for i in range(levels)]
        c = [[] for i in range(levels)]

        all_colors = [color['name'] for color in db.color_names()]

        c[0].append(all_colors)
        res, incr = speed_results(n, lasers, c[0][0])
        counter += incr
        r[0].append(res)
        for l in range(1,levels):
            print("*" * 15 + " Level " + str(l) + " " + "*" * 15)
            print()
            for res_i,res in enumerate(r[l-1]):

                for col_i,col in enumerate(res):
                    print("n: {6}, Level: {0}/{5}, result: {3}/{4}, color: {1}/{2}:{10} || color list length: {7} || {8} data added, run time: {9} seconds"
                          .format(l, col_i+1, len(res),res_i+1,len(r[l-1]),levels-1,n,len(c[l-1][res_i]),counter,int(time.time()-start),col))



                    col_list = c[l - 1][res_i]
                    index = col_list.index(col)
                    a = col_list[:index] + col_list[index + 1:]
                    c[l].append(a)
                    res, incr = speed_results(n, lasers, a)

                    r[l].append(res)
                    counter += incr
                print("-"*39)














