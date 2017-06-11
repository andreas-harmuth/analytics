from django.db import connection
import sqlite3
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
        sql = 'create table if not exists fluorochromes_all (colorID TEXT, wavelength INTEGER, excitation INTEGER, emission INTEGER)'  # Create the sql tables
        self.cursor.execute(sql)
        print('Analytics database started')



    # Todo: delete (hashed table of all data contains this)
    def color_names(self):
        # Run the SQL that takes all the information from the fluorochromes_all table
        sql = 'SELECT colorID FROM fluorochromes_all'
        self.cursor.execute(sql)

        # List of names
        names_list = list()

        # Fetch all the information and hash it
        for row in self.cursor.fetchall():

            # Append the cell corresponding to the colorID-name
            names_list.append(row[0])

        # Set returns the unit set of name. We list it after to get the output as a list
        # Todo: Fix the algorithm, we check if the data is already in names_list
        return list(set(names_list))




    def fetch_all_data(self):

        # The object that will stored the hashed information. Here the key is the colorID
        data_dict = dict()

        # Run the SQL that takes all the information from the fluorochromes_all table
        sql = 'SELECT * FROM fluorochromes_all'
        self.cursor.execute(sql)

        # Fetch all the information and hash it
        for row in self.cursor.fetchall():

            # todo: optimize with numpy?

            data_dict.setdefault(row[0], []).append(row[1:4])
            #data_dict.setdefault(row[0], [[],[],[]])[0].append(int(row[1]))
            #data_dict[row[0]][1].append(float(row[2]))
            #data_dict[row[0]][2].append(float(row[3]))





        return data_dict




    def update_data(self,input_file):
        # Get all the data in a hash table
        all_data = self.fetch_all_data()

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












