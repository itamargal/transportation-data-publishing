#  merge convereted xlsx to csv files into one master doc
#  make sure to handle date and time columns properly

import os
 
rootDir = 'converted/'

count = 0
with open('master_xlsx_list.csv', 'w') as outfile:
    for dirpath, subdirs, files in os.walk(rootDir):

        for fname in files:
            if fname.endswith('.csv') and 'TripReport' in fname:
                count += 1
                f = os.path.join(dirpath, fname)

                with open(f, 'r') as temp:
                    if count==1:
                        for line in temp:
                            outfile.write(line)
                    
                    else:
                        temp.next()
                        for line in temp:
                            outfile.write(line)

