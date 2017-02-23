import csv
import pdb

lookup = {}
unknown_kiosks = []
out_data = []

fieldnames = ['Trip ID', 'Membership Type', 'Bike', 'Checkout Date', 'Checkout Time', 'Checkout Kiosk ID', 'Checkout Kiosk', 'Return Kiosk ID', 'Return Kiosk', 'Duration (Minutes)']


with open('kiosks.csv', 'r') as infile:
    reader = csv.DictReader(infile)

    for row in reader:
        key = row['kiosk_name']
        key_id = row['kiosk_id']
        lookup[key] = key_id

count = 0

with open('master_xlsx_list.csv', 'r') as infile:
    reader = csv.DictReader(infile)

    with open('master_list_w_lookups.csv', 'w') as outfile:

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            count +=1

            if 'Checkout Kiosk' in row:
                checkout_kiosk = row['Checkout Kiosk']

            if 'Return Kiosk' in row.keys():
                return_kiosk = row['Return Kiosk']

            if return_kiosk:
                if checkout_kiosk in lookup:
                    checkout_id = lookup[checkout_kiosk]
                    row['Checkout Kiosk ID'] = checkout_id
                else:
                    if checkout_kiosk not in unknown_kiosks:
                        unknown_kiosks.append(checkout_kiosk)

            if return_kiosk:
                if return_kiosk in lookup:
                    return_id = lookup[return_kiosk]
                    row['Return Kiosk ID'] = return_id

                else:
                    if return_kiosk not in unknown_kiosks:
                        unknown_kiosks.append(return_kiosk)

            out_data.append(row)

        for row in out_data:
            writer.writerow(row)

















