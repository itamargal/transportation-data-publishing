#  status duration
#  dont upload if no data
#  enable request verification
#  fieldnames! e.g. atd_intersection_id
#  dodgy error handling in change detection
#  use ATD intersection ID as row identifier
#  append new intersections to historical dataset?

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import pymssql
import pyodbc
import arrow
import requests
import json
import email_alert
from secrets import KITS_CREDENTIALS
from secrets import SOCRATA_CREDENTIALS
from secrets import ALERTS_DISTRIBUTION
from secrets import IDB_PROD_CREDENTIALS

import pdb

SOCRATA_SIGNAL_STATUS = 'https://data.austintexas.gov/resource/5zpr-dehc.json'
SOCRATA_SIGNAL_STATUS_HISTORICAL = 'https://data.austintexas.gov/resource/x62n-vjpq.json'
SOCRATA_PUB_LOGS = 'https://data.austintexas.gov/resource/n5kp-f8k4.json'

EMAIL_FOOTER = '''
    \n
    This is an automated message generated by Austin Transportation's Arterial Management Division. To unsubscribe, contact john.clary@austintexas.gov.
    '''

then = arrow.now()
logfile_filename = 'logs/signals-on-flash/{}.csv'.format(then.format('YYYY-MM-DD'))



def fetch_kits_data():
    print('fetch kits data')

    conn = pymssql.connect(
        server=KITS_CREDENTIALS['server'],
        user=KITS_CREDENTIALS['user'],
        password=KITS_CREDENTIALS['password'],
        database=KITS_CREDENTIALS['database']
    )

    cursor = conn.cursor(as_dict=True)

    search_string = '''
        SELECT i.INTID as database_id
            , e.DATETIME as status_datetime
            , e.STATUS as intersection_status
            , i.POLLST as poll_status
            , e.OPERATION as operation_state
            , e.PLANID as plan_id
            , i.STREETN1 as primary_street
            , i.STREETN2 as secondary_street
            , i.ASSETNUM as atd_intersection_id
            , i.LATITUDE as latitude
            , i.LONGITUDE as longitude
            FROM [KITS].[INTERSECTION] i
            LEFT OUTER JOIN [KITS].[INTERSECTIONSTATUS] e
            ON i.[INTID] = e.[INTID]
            ORDER BY e.DATETIME DESC
    '''

    cursor.execute(search_string)  

    return cursor.fetchall()



def fetch_published_data():
    print('fetch published data')
    try:
        res = requests.get(SOCRATA_SIGNAL_STATUS, verify=False)

    except requests.exceptions.HTTPError as e:
        raise e

    return res.json()



def reformat_kits_data(dataset):
    print('reformat data')
    
    reformatted_data = []
    
    for row in dataset:        
        formatted_row = {}

        for key in row:
            new_key = str(key)
            new_value = str(row[key])
            formatted_row[new_key] = new_value
        
        reformatted_data.append(formatted_row)

    return reformatted_data



def group_data(dataset, key):
    print('group data')

    grouped_data = {}
    
    for row in dataset:
        new_key = str(row[key])
        grouped_data[new_key] = row

    return grouped_data



def check_for_stale_data(dataset):
    print('check for stale data')

    status_times = []

    for record in dataset:
        if record['status_datetime']:
            compare = arrow.get(record['status_datetime'])
            status_times.append(compare)

    oldest_record =  arrow.get(max(status_times)).replace(tzinfo='US/Central')  #  have to swap TZ info here because the database query is incorrectly storing datetimes as UTC

    delta = arrow.now() - oldest_record

    delta_minutes = delta.seconds/60

    if delta_minutes > 15:  #  if more than 15 minutes have passed since a status update

        subject = 'DATA PROCESSING ALERT: KITS Status Data is {} mintues old'.format(str(delta_minutes))

        body = 'DATA PROCESSING ALERT: KITS intersection status data has not been updated for more than {} minutes.'.format(str(delta_minutes))

        body = body + EMAIL_FOOTER

        email_alert.send_email(ALERTS_DISTRIBUTION, subject, body)



def detect_changes(new, old):
    print('detect changes')

    upsert = []  #  see https://dev.socrata.com/publishers/upsert.html
    not_processed = []
    no_update = 0  
    insert = 0
    update= 0
    delete = 0    
    upsert_historical = []

    for record in new:  #  compare KITS to socrata data
        lookup = str(new[record]['database_id'])

        if lookup in old:
            new_status = str(new[record]['intersection_status'])
            #  new_status = str(9999)  #  tests

            try:
                old_status = str(old[lookup]['intersection_status'])

            except:
                not_processed.append(new[record]['database_id'])
                continue
            
            if new_status == old_status:
                no_update += 1
            
            else:
                update += 1
                new[record]['intersection_status_previous'] = old_status
                upsert.append(new[record])
                upsert_historical.append(old[lookup])
            
        else:
            insert += 1
            upsert.append(new[record])

    for record in old:  #  compare socrata to KITS to idenify deleted records
        lookup = old[record]['database_id']
        
        if lookup not in new:
            delete += 1

            upsert.append({ 
                'database_id': lookup,
                ':deleted': True
            })

    return { 
        'upsert': upsert,
        'not_processed': not_processed,
        'insert': insert,
        'update': update,
        'no_update':  no_update,
        'delete': delete,
        'upsert_historical': upsert_historical
    }



def connect_int_db(credentials):
    print('connecting to intersection database')

    conn = pyodbc.connect(
        'DRIVER={{SQL Server}};' 
            'SERVER={};'
            'PORT=1433;'
            'DATABASE={};'
            'UID={};'
            'PWD={}'
            .format(
                credentials['server'],
                credentials['database'],
                credentials['user'],
                credentials['password'] 
        ))

    cursor = conn.cursor()
    
    return conn



def prep_int_db_query(upsert_data):
    ids = []
    
    print('prep intersection database query')

    for row in upsert_data:
        ids.append(row['atd_intersection_id'])

    where = str(ids).translate(None, "[]")

    query  = '''
        SELECT * FROM GIS_QUERY
        WHERE GIS_QUERY.ATD_INTERSECTION_ID IN ({})
    '''.format(where)

    return query



def get_int_db_data_as_dict(connection, query, key):

    print('get intersection database data')
    
    results = []

    grouped_data = {}

    cursor = connection.cursor()
    
    cursor.execute(query)

    columns = [column[0] for column in cursor.description]
    
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    for row in results:  #  sloppy conversion of sql object
        
        for val in row:
            
            try:
                row[val] = str(row[val])

            except (ValueError, TypeError):
                pass
            
            if row[val] == 'None':
                row[val] = ''

            try:
                if row[val][-2:] == '.0':
                    row[val] = row[val].replace('.0','')
            except:
                pass

            if val == key:
                new_key = row[key]

        grouped_data[new_key] = row
    
    return grouped_data



def prepare_socrata_payload(upsert_data, int_db_data):
    print('prepare socrata payload')
    
    not_found = []

    now = arrow.now()
    

    for row in upsert_data:
        atd_intersection_id = row['atd_intersection_id']
        row['processed_datetime']  = now.format('YYYY-MM-DD HH:mm:ss')
        row['record_id'] = '{}_{}'.format(row['atd_intersection_id'], str(now.timestamp))
        if atd_intersection_id in int_db_data:
            row['processed_datetime']  = now.format('YYYY-MM-DD HH:mm:ss')
            row['record_id'] = '{}_{}'.format(row['atd_intersection_id'], str(now.timestamp))
            row['primary_street'] = int_db_data[atd_intersection_id]['STREET_SEGMENTS.FULL_STREET_NAME']
    
            if int_db_data[atd_intersection_id]['STREET_SEGMENTS_1.FULL_STREET_NAME']:
                row['cross_street'] = int_db_data[atd_intersection_id]['STREET_SEGMENTS_1.FULL_STREET_NAME']
                row['intersection_name'] = row['primary_street'] + " / " + row['cross_street']
            else:
                row['intersection_name'] = row['primary_street'] + " (NO CROSS ST)"

            row['latitude'] = int_db_data[atd_intersection_id]['LATITUDE']
            row['latitude'] = int_db_data[atd_intersection_id]['LONGITUDE']

        else:
            not_found.append(atd_intersection_id)
            upsert_data.remove(row)

    return (upsert_data, not_found)



def upsert_open_data(payload, url):
    print('upsert open data ' + url)
    
    try:
        auth = (SOCRATA_CREDENTIALS['user'], SOCRATA_CREDENTIALS['password'])

        json_data = json.dumps(payload)

        res = requests.post(url, data=json_data, auth=auth, verify=False)

    except requests.exceptions.HTTPError as e:
        raise e
    
    return res.json()



def package_log_data(date, changes, response):
    
    timestamp = arrow.now().timestamp

    date = date.format('YYYY-MM-DD HH:mm:ss')
   
    if 'error' in response.keys():
        response_message = response['message']
        
        email_alert.send_email(ALERTS_DISTRIBUTION, 'DATA PROCESSING ALERT: Socrata Upload Status Update Failure', response_message + EMAIL_FOOTER)

        errors = ''
        updated = ''
        created = ''
        deleted = ''

    else:
        errors = response['Errors']
        updated = response['Rows Updated']
        created = response['Rows Created']
        deleted = response['Rows Deleted']
        response_message = ''

    no_update = changes['no_update']
    update_requests = changes['update']
    insert_requests = changes['insert']
    delete_requests = changes['delete']

    if changes['not_processed']:
        not_processed = str(changes['not_processed'])
    else:
        not_processed = ''
     
    return [ {
        'event': 'signal_status_update',
        'timestamp': timestamp, 
        'date_time':  date,
        'errors': errors ,
        'updated': updated,
        'created': created,
        'deleted': deleted,
        'no_update': no_update,
        'not_processed': not_processed,
        'response_message': response_message
    } ]

    

    
def main(date_time):
    print('starting stuff now')

    try:
        new_data = fetch_kits_data()

        new_data_reformatted = reformat_kits_data(new_data)
        
        check_for_stale_data(new_data)
        
        new_data_grouped = group_data(new_data_reformatted, 'database_id')
                
        old_data = fetch_published_data()

        old_data_grouped = group_data(old_data, 'database_id')

        change_detection_results = detect_changes(new_data_grouped, old_data_grouped)

        conn = connect_int_db(IDB_PROD_CREDENTIALS)

        int_db_query = prep_int_db_query(change_detection_results['upsert'])

        int_db_data = get_int_db_data_as_dict(conn, int_db_query, 'ATD_INTERSECTION_ID')

        socrata_payload = prepare_socrata_payload(change_detection_results['upsert'], int_db_data)

        socrata_response = upsert_open_data(socrata_payload[0], SOCRATA_SIGNAL_STATUS)

        socrata_response_historical = upsert_open_data(change_detection_results['upsert_historical'], SOCRATA_SIGNAL_STATUS_HISTORICAL)

        logfile_data = package_log_data(date_time, change_detection_results, socrata_response)

        logfile_response = upsert_open_data(logfile_data, SOCRATA_PUB_LOGS)

        return {
            'res': socrata_response,
            'res_historical': socrata_response_historical,
            'payload': socrata_payload[0],
            'logfile': logfile_data,
            'not_found': socrata_payload[1]
        }
    
    except Exception as e:
        print('Failed to process data for {}'.format(date_time))
        print(e)
        email_alert.send_email(ALERTS_DISTRIBUTION, 'DATA PROCESSING ALERT: Signal Status Update Failure', str(e) + EMAIL_FOOTER)
        raise e
 


results = main(then)

print(results['res'])
print('Elapsed time: {}'.format(str(arrow.now() - then)))
