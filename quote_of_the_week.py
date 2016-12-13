#  download quotes of the week from knack
#  find the latest
#  commit it to github

import arrow
import requests
import data_helpers
import csv
from StringIO import StringIO
#  import github_updater
#  import knack_helpers
import secrets

import pdb

REPO_URL_GITHUB = 'https://api.github.com/repos/cityofaustin/transportation-logs/contents/'
DATA_URL_GITHUB = 'https://raw.githubusercontent.com/cityofaustin/transportation-logs/master/'
DATASET_FIELDNAMES = ['date_time', 'socrata_errors', 'socrata_updated', 'socrata_created', 'socrata_deleted', 'no_update', 'update_requests', 'insert_requests', 'delete_requests', 'not_processed','response_message']


#  KNACK CONFIG
KNACK_PARAMS = {  
    'REFERENCE_OBJECTS' : ['object_11', 'object_12'],
    'SCENE' : '73',
    'VIEW' : '197',
    'FIELD_NAMES' : ['ATD_LOCATION_ID','ATD_SIGNAL_ID','COA_INTERSECTION_ID','CONTROL','COUNCIL_DISTRICT', 'CROSS_ST','CROSS_ST_AKA','CROSS_ST_SEGMENT_ID','JURISDICTION','LANDMARK','LOCATION_NAME','PRIMARY_ST', 'PRIMARY_ST_AKA','PRIMARY_ST_SEGMENT_ID','SIGNAL_ENG_AREA','SIGNAL_STATUS','SIGNAL_TYPE','TRAFFIC_ENG_AREA','MASTER_SIGNAL_ID', 'GEOCODE', 'IP_SWITCH', 'IP_CONTROL', 'SWITCH_COMM', 'COMM_PLAN', 'TURN_ON_DATE', 'MODIFIED_DATE', 'CROSS_ST_BLOCK', 'PRIMARY_ST_BLOCK', 'COUNTY'],
    'APPLICATION_ID' : secrets.KNACK_CREDENTIALS['APP_ID'],
    'API_KEY' : secrets.KNACK_CREDENTIALS['API_KEY']
}


then = arrow.now()


def main(date_time):
    print('starting stuff now')

    try:
        url = 'https://raw.githubusercontent.com/cityofaustin/transportation/gh-pages/components/data/quote_of_the_week.csv'
        
        data = data_helpers.GetWebCSV(url)

        newest = {}

        newest['quote_date'] = arrow.get('1/1/1900')

        for row in data:
            
            if 'quote_date' in row:
        
                this_time = arrow.get(row['quote_date'], 'MM/DD/YYYY')
                
                if this_time.timestamp > newest['quote_date'].timestamp:
                    newest = row

        print(newest)

        #  update github with neweset quote data
        #  update publication log, too

        pdb.set_trace()
        return 'youve got the newest now'

    except Exception as e:
        print('Failed to process data for {}'.format(date_time))
        print(e)
        raise e
 

results = main(then)

print('Elapsed time: {}'.format(str(arrow.now() - then)))


