import csv
import pdb


master_file = 'wow_mega_master_list.csv'
trip_gen_file = 'master_with_trips.csv'

id_gen = 9900000000

with open(master_file, 'r') as infile:
    reader = csv.DictReader(infile)
    
    fieldnames = reader.fieldnames
        
    with open(trip_gen_file, 'w') as outfile:

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
    
        for row in reader:
            if not row['Trip ID']:
                row['Trip ID'] = str(id_gen)
                id_gen += 1
        
            writer.writerow(row)






