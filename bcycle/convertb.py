#  need to write full six-digt time strings otherwise
#  you get shit like 4:4:2
import os
import xlrd
import csv
import pdb
    
date_cols = [2, 3]


def excel_time_to_string(xltimeinput, datemode, col_num):
        #  check col num and either convert to date or time
        try:
            col_date = xlrd.xldate.xldate_as_datetime(xltimeinput, datemode)

            if col_num == 2:    
                col_date_string = '{}/{}/{}'.format(col_date.month, col_date.day, col_date.year)

            elif col_num == 3:
                #  col_date_string = '{}/{}/{} {}:{}:{}'.format('01', '01', '2000', col_date.strftime('%H'), col_date.strftime('%m'), col_date.strftime('%S'))
                col_date_string = '{}:{}:{}'.format(col_date.strftime('%H'), col_date.strftime('%m'), col_date.strftime('%S'))
            else:
                return xltimeinput

            return col_date_string

        except TypeError:
            print(xltimeinput)
            return xltimeinput



def csv_from_excel(in_dir, infile, out_dir):
    
    xlsx = os.path.join(in_dir, infile)    
    wb = xlrd.open_workbook(xlsx)
    sh = wb.sheet_by_index(0)

    outname = infile.replace('.xlsx', '.csv')
    outfile = os.path.join(out_dir, outname) 
    
    with open(outfile, 'w') as out_csv:
        #  http://stackoverflow.com/questions/28609367/read-xls-convert-all-dates-into-proper-format-write-to-csv
        wr = csv.writer(out_csv, quoting=csv.QUOTE_ALL)

        for rownum in range(sh.nrows):
            cell_values = wb.sheet_by_index(0).row_values(rownum)
       
            for col in date_cols:
                cell_values[col] = excel_time_to_string(cell_values[col], wb.datemode, col)

            wr.writerow(cell_values)



rootDir = '/Users/John/Dropbox/AustinBcycleTripData'
outDir = '/Users/John/Desktop/converted'



for dirpath, subdirs, files in os.walk(rootDir):
    for fname in files:
        if fname.endswith('.xlsx') and 'TripReport' in fname:

            csv_from_excel(dirpath, fname, outDir)





