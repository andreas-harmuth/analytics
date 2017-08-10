import sqlite3,json,itertools
import numpy as np
from operator import itemgetter
"""
    Main database for data
    
    Raw SQLite compared to Django Model
"""


# If a needle is found the return the index of that needle, otherwise return -1
def find_needle(needle,haystack):


    for index,hay in enumerate(haystack):
        if needle == hay:
            # return index
            return index

    # No needle, return -1
    return -1







class dataDB:

    def __init__(self):
        # db_init will create the database before initing anything

        self.conn = sqlite3.connect('./fluorochromes_data.db')
        self.cursor = self.conn.cursor()

        # Create the tabels for fluorochromes_all with the appropriate columns
        sql = 'create table if not exists fluorochromes_all (colorID TEXT, wavelength INTEGER, excitation INTEGER,' \
              ' emission INTEGER, category TEXT, suggest INTEGER)'  # Create the sql tables
        self.cursor.execute(sql)


        # Create a log for basic combinations
        sql = 'create table if not exists basic_comb_log (color_numbers INTERGER, laser TEXT, colors TEXT, saved_data TEXT)'  # Create the sql tables
        self.cursor.execute(sql)

        # Create a log for performance
        sql = 'create table if not exists performance_log (time_in_ms REAL, combinations INTEGER , processor TEXT)'  # Create the sql tables
        self.cursor.execute(sql)




        ######## auto generated data #######

        # n range
        sql = 'create table if not exists agd_n (n INTEGER)'
        self.cursor.execute(sql)

        # Fluorochromes
        sql = 'create table if not exists agd_fc (fc TEXT)'
        self.cursor.execute(sql)

        # Lasers
        sql = 'create table if not exists agd_lasers (lasers TEXT)'
        self.cursor.execute(sql)


    # Todo: delete (hashed table of all data contains this)
    def color_names(self):
        # Run the SQL that takes all the information from the fluorochromes_all table
        sql = 'SELECT colorID,category,suggest FROM fluorochromes_all'
        self.cursor.execute(sql)

        # List of names
        names_list = list()
        pass_list = list()
        # Fetch all the information and hash it
        for row in self.cursor.fetchall():

            # Append the cell corresponding to the colorID-name
            if row[0] not in pass_list:
                names_list.append({"name":row[0],"category":row[1],"suggest":1==row[2]})
                pass_list.append(row[0])
        # Set returns the unit set of name. We list it after to get the output as a list

        return names_list




    def fetch_all_data(self,by="row"):

        # The object that will stored the hashed information. Here the key is the colorID
        data_dict = dict()

        # Run the SQL that takes all the information from the fluorochromes_all table
        sql = 'SELECT * FROM fluorochromes_all'
        self.cursor.execute(sql)

        # Fetch all the information and hash it
        for row in self.cursor.fetchall():
            # todo: optimize with numpy -> db with 3, and analysis with first?
            if by == "row":

                data_dict.setdefault(row[0], []).append(row[1:4])
            elif by == "col":
                data_dict.setdefault(row[0], [[],[],[]])[0].append(int(row[1]))
                data_dict[row[0]][1].append(float(row[2]))
                data_dict[row[0]][2].append(float(row[3]))



        return data_dict




    def update_data(self,input_file):
        # Get all the data in a hash table
        all_data = self.fetch_all_data(by="col")


        # Extract all names
        name_list = [name for name in all_data]
        file = open(input_file, "r")
        f = file.read()


        # Get all rows
        all_rows = f.split("\n")

        status = {'updated': 0,
                  'added': 0}

        # Split the input files by rows
        for done,row in enumerate(all_rows):

            #print((round(done/total)*100))
            data = row.split("/,/")


            if data[0] in name_list:


                # This is to optimize the next, next (*) if
                needle_index = find_needle(int(data[1]),all_data[data[0]][0])


                # If a needle is found
                if needle_index != -1:


                    #(*) use the needle to see if the data is different than the current one
                    if(int(data[1]) != all_data[data[0]][0][needle_index] or float(data[2]) != all_data[data[0]][1][needle_index]
                       or float(data[3]) != all_data[data[0]][2][needle_index]):

                        sql = """
                            UPDATE fluorochromes_all
                            SET excitation=?, emission=?
                            WHERE colorID=? AND wavelength=? 
                        """
                        status['updated'] +=1

                    else:
                        sql = 'false'

                else:
                    status['added'] += 1
                    sql = 'INSERT INTO fluorochromes_all (excitation, emission,colorID, wavelength) VALUES(?,?,?,?)'
            else:
                status['added'] += 1

                sql = 'INSERT INTO fluorochromes_all (excitation, emission,colorID, wavelength) VALUES(?,?,?,?)'



            # todo: improve this
            if sql != 'false':

                self.cursor.execute(sql, [float(data[2]),float(data[3]),str(data[0]),int(data[1])])


        self.conn.commit()
        print("{0} updated data and {1} added data.".format(status['updated'],status['added']))
        file.close()

        return status

    def fetch_fluorchromes_data(self, color_list):
        # As the SQL-syntax has a WHERE statement, than are going to take multiple inputs. This string is generated below



        sql = """SELECT 
                    * 
                FROM 
                    fluorochromes_all
                WHERE
                    colorID IN (
                    """+",".join(["?"]*len(color_list))+")"

        self.cursor.execute(sql,color_list)

        # temporary dictionary holder
        temp_dict = {}


        # Below we convert all the rows of data into a dictionary where the key is the color name ie, "Alexa Fluor 430"
        # The value is a (numpy) matrix of the data with the columns: wavelength, excitation, emission
        for row in self.cursor.fetchall():
            row = list(row)

            # Here we set the emission to 0 if it is below 0
            if row[2] < 0:
                row[2] = 0
            try:
                # Todo: Timetest to see if try/except is faster or slower than (if x in dict).

                # If a key does exist for the dictionary then append the row to the correct matrix
                temp_dict[row[0]] = np.vstack((temp_dict[row[0]], row[1:4]))

            except:
                # If the key did not exists then the code would fail and jump to this part which init the numpy
                # matrix as a single row

                temp_dict[row[0]] = np.array(row[1:4])


        return temp_dict



    # Test function that returns all the data
    def fetch_fluorchromes_data_test(self, color_list):
        # As the SQL-syntax has a WHERE statement, than are going to take multiple inputs. This string is generated below



        sql = """SELECT * FROM fluorochromes_all"""

        self.cursor.execute(sql)

        # temporary dictionary holder
        temp_dict = {}


        # Below we convert all the rows of data into a dictionary where the key is the color name ie, "Alexa Fluor 430"
        # The value is a (numpy) matrix of the data with the columns: wavelength, excitation, emission
        for row in self.cursor.fetchall():
            row = list(row)

            # Here we set the emission to 0 if it is below 0
            if row[3] < 0:

                row[3] = 0

            try:


                # If a key does exist for the dictionary then append the row to the correct matrix
                temp_dict[row[0]] = np.vstack((temp_dict[row[0]], row[1:4]))

            except:
                # If the key did not exists then the code would fail and jump to this part which init the numpy
                # matrix as a single row

                temp_dict[row[0]] = np.array(row[1:4])


        return temp_dict


    def add_basic_comb_log(self,cn,l,c,new_data):
        #sql = 'create table if not exists basic_comb_log (color_numbers INTERGER, laser TEXT, colors TEXT, saved_data TEXT)'
        laser = json.dumps(l)
        colors = json.dumps(c)


        new_data_list = json.dumps([obj_data.name for obj_data in new_data])




        sql = 'INSERT INTO basic_comb_log (color_numbers, laser, colors, saved_data) VALUES(?,?,?,?)'

        self.cursor.execute(sql, [cn,laser,colors,new_data_list])
        self.conn.commit()



    # Check if any subset of the combination is already in the database
    def extended_check_basic_comb_log(self, cn, l, c):

        # Dumb the laser, so it matches the format of SQL-data. Remember this is sorted
        laser = json.dumps(l)

        # We are not dumbing the laser as we want to check it as a regular list later
        colors = c

        # Prepare the query
        sql = """SELECT 
                    colors, saved_data
                FROM 
                    basic_comb_log
                WHERE
                     color_numbers=? AND laser=?"""


        # Fetch all data with this specific laser and n value. This is the smallest sample we can obtain from the given info
        self.cursor.execute(sql, [cn, laser])

        # Fetch all the lasers
        fetched_data_set = self.cursor.fetchall()

        for fetched_data in fetched_data_set:

            # Check if the all the elements in the input is present in the color combination of the current comb. Also check
            # if the resulting colors are present in the results
            # fetched_data[0] = colors (fc)
            # fetched_data[1] = results

            if all(fc in json.loads(fetched_data[0]) for fc in colors) and all(fc in colors for fc in json.loads(fetched_data[1])):
                #print("Debug: found")
                # If any is found, then return the list.
                return fetched_data[1]

        return None


    def update_suggest(self,fc_list):
        counter = 0
        for fc in fc_list:

            sql = """UPDATE
              fluorochromes_all
            SET
              suggest = ?
            WHERE
              colorID = ?
            """
            counter +=1
            self.cursor.execute(sql, [fc_list[fc],fc])


        self.conn.commit()






    def speed_test(self,t,c,p):
        # t = time
        # c = combinations
        # p = processor

        sql = 'INSERT INTO performance_log (time_in_ms, combinations, processor) VALUES(?,?,?)'
        self.cursor.execute(sql, [t,c,p])
        self.conn.commit()
        #print(t,c,p)



    def get_performance(self):
        sql = 'SELECT * FROM performance_log ORDER BY time_in_ms'

        self.cursor.execute(sql)

        data_dict = {}

        for row in self.cursor.fetchall():
            data_dict.setdefault(row[2],{'time':[],'combinations':[]})['time'].append(row[0])
            data_dict[row[2]]['combinations'].append(row[1])

        return data_dict



    def get_statistics(self):

        sql = " SELECT * FROM basic_comb_log"

        # Fetch all data
        self.cursor.execute(sql)


        combinations = len(self.cursor.fetchall())
        fluorochromes = len(self.color_names())

        return {'combinations'      :   combinations,
                'fluorochromes '    :   fluorochromes }


    def join_combination(self,n_small,n_big,lasers,fc_start = None):

        tables = ['agd_n','agd_fc','agd_lasers']
        for table in tables:
                sql = 'DELETE FROM ' + table
                self.cursor.execute(sql)
        sql = "DROP TABLE if exists all_options"
        self.cursor.execute(sql)

        for n in range(n_small,n_big):
            sql = 'INSERT INTO agd_n (n) VALUES(?)'
            self.cursor.execute(sql,[n,])

        for laser in lasers:
            sql = 'INSERT INTO agd_lasers (lasers) VALUES(?)'
            self.cursor.execute(sql, [json.dumps(laser), ])

        fc_list = [fc['name'] for fc in self.color_names()]

        if fc_start != None:
            print("Multiple colors")
            for fc_i in range(len(fc_list)-fc_start,len(fc_list)):
                print(fc_i)

                m_comb = list(itertools.combinations(range(len(fc_list)), fc_i))

                print(len(m_comb))
                for comb in m_comb:




                    sql = 'INSERT INTO agd_fc (fc) VALUES(?)'

                    self.cursor.execute(sql, [json.dumps([fc_list[i] for i in comb]), ])
        else:
            print("All color only")
            self.cursor.execute(sql, [json.dumps(fc_list), ])


        sql = "CREATE TABLE if not exists all_options as SELECT * FROM agd_n, agd_lasers, agd_fc"
        self.cursor.execute(sql)

        sql = 'SELECT * FROM all_options'

        self.cursor.execute(sql)
        comb = self.cursor.fetchall()

        print('The database \"all_options\" have been created. It contains {0} number of solutions (rows).'.format(
            len(comb)))

        return comb

        # Cleans up the database
    def clean_up(self):
        sql = 'DROP TABLE IF EXISTS clean_up_copy;'
        self.cursor.execute(sql)

        sql = 'CREATE TABLE clean_up_copy AS SELECT DISTINCT * FROM basic_comb_log'
        self.cursor.execute(sql)

        sql = 'SELECT * FROM clean_up_copy'

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        print(rows[1])
        # row[0] = n
        # row[1] = laser
        # row[2] = input colors
        # row[3] = results

        results_hash = {}
        print(results_hash)
        # Sort them in a hashtable
        for row in rows:
            results_hash.setdefault(json.dumps([row[0],row[1],row[3]]),[]).append(json.loads(row[2]))

        for results in results_hash:

            if len(results_hash[results]) != 1:

                # Sort the results by the length of the list. It takes the smallest first so we simply reverse it
                results_hash[results] = sorted(results_hash[results], key=len,reverse=True)

                elim_list = [] # List with indices that will be eliminated

                for index_parent,input_color_list in enumerate(results_hash[results]):
                    # If a list "under" this list is in # ONLY CHECK UNDER -> write [i-j]
                    # If the small list is in the big list, then delete the small list
                    for index, compare_list in enumerate(results_hash[results]):
                        if all(fc in input_color_list for fc in compare_list) and index != index_parent:

                            elim_list.append(index)
                if elim_list != []:

                    for index in sorted(elim_list, reverse=True):
                        del results_hash[results][index]

        sql = "DELETE FROM clean_up_copy"
        self.cursor.execute(sql)


        for results in results_hash:

            row = json.loads(results)

            # row[0] = n
            # row[1] = laser
            # row[2] = results
            # dict[key] = colors
            laser = json.dumps(row[1])

            new_data_list = row[2]

            for colors in (results_hash[results]):
                sql = 'INSERT INTO clean_up_copy (color_numbers, laser, colors, saved_data) VALUES(?,?,?,?)'

                self.cursor.execute(sql, [row[0], laser, json.dumps(colors), new_data_list])

        self.conn.commit()
        # Sort each hashtable by len of inputcolor:
        #sorted(data, key=itemgetter(1))









# Test list
#"7-AAD (7-aminoactinomycin D)", "eFluor 660", "Alexa Fluor 405", "Alexa Fluor 594", "Alexa Fluor 430", "APC-Alexa Fluor 750"

db = dataDB()
db.clean_up()

#db.update_suggest(fc_list)
#db.update_data('./data.txt') # Update the database with given data

#db.fetch_fluorchromes_data_test(1)
#db.fetch_fluorchromes_data(["7-AAD (7-aminoactinomycin D)", "eFluor 660", "Alexa Fluor 405", "Alexa Fluor 594", "Alexa Fluor 430", "APC-Alexa Fluor 750"])