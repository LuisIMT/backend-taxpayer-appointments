from generate_data import gen_data
from config import settings
import json
import os
import pandas as pd

def main():
    data = gen_data( seed = 0 )
    data.faker_data()
    with open( os.path.join( os.path.dirname(__file__), "taxpayers.json" ) ) as f:
        df = json.load( f )
    dataset = pd.json_normalize( df )
    list_client = data.calculate_scores( df = dataset,
                                        office_location = ( settings[ 'office' ][ 'latitude' ], settings[ 'office' ][ 'longitude' ] )
                                        )
    print ( list_client )
    json_data = list_client.to_json(orient='records')
    with open( os.path.join( os.path.dirname( __file__ ), "client_list.json" ) , "w" ) as outfile:
            json.dump( json_data, outfile, indent=4 )
if __name__ == '__main__':
    main()
