# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

@shared_task
def celery_twist_sum(auc_overlaps, comb, c_min):


    # TODO: implement the the search part as well
    counter = 0
    n = len(comb)

    for j in range(n - 1):
        for i in range(j + 1, n):

            counter += (auc_overlaps[comb[i], comb[j]])
            if c_min < counter:
                # no need to do further calculations if the counter is already bigger then then min
                # print(j)
                return counter

    return counter