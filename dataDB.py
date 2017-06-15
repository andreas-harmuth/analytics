from django.db import connection
import sqlite3
import numpy as np
"""
    Main database for data
    
    Raw SQLite compared to Django Model
"""


# If a needle is found the return the index of that needle, otherwise return -1
def find_needle(needle,haystack):


    for index,hay in enumerate(haystack):
        #print(index,hay)
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




    def fetch_all_data(self,by="row"):

        # The object that will stored the hashed information. Here the key is the colorID
        data_dict = dict()

        # Run the SQL that takes all the information from the fluorochromes_all table
        sql = 'SELECT * FROM fluorochromes_all'
        self.cursor.execute(sql)

        # Fetch all the information and hash it
        for row in self.cursor.fetchall():

            # todo: optimize with numpy -> db with 3, and analysis with first?
            if by == "rows":

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
                #print(data[0])

                #print(all_data[data[0]][0])
                #print(all_data[data[0]])
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
                # Todo: Timetest to see if try/except is faster or slower than (if x in dict).

                # If a key does exist for the dictionary then append the row to the correct matrix
                temp_dict[row[0]] = np.vstack((temp_dict[row[0]], row[1:4]))

            except:
                # If the key did not exists then the code would fail and jump to this part which init the numpy
                # matrix as a single row

                temp_dict[row[0]] = np.array(row[1:4])


        return temp_dict






# Test list
#"7-AAD (7-aminoactinomycin D)", "eFluor 660", "Alexa Fluor 405", "Alexa Fluor 594", "Alexa Fluor 430", "APC-Alexa Fluor 750"
#db = dataDB()
#db.update_data('./data.txt') # Update the database with given data

#db.fetch_fluorchromes_data_test(1)
#db.fetch_fluorchromes_data(["7-AAD (7-aminoactinomycin D)", "eFluor 660", "Alexa Fluor 405", "Alexa Fluor 594", "Alexa Fluor 430", "APC-Alexa Fluor 750"])