from faker import Faker
import json
import os
from haversine import haversine
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from config import settings

class gen_data:
    def __init__( self, seed ) -> None:
        self.seed : int = seed

    def faker_data( self ) -> None:

        fake = Faker()
        Faker.seed( self.seed )

        taxpayers = []

        for _ in range( 1000 ):
            geolocation = fake.local_latlng( country_code = "MX" )
            taxpayer = {
                "id" : fake.uuid4(),
                "name" : fake.name(),
                "location" : {
                "latitude" : float( geolocation[ 0 ] ),
                "longitude":float( geolocation[ 1 ] )
                },
                "age" : fake.random_int( 18, 90 ),
                "accepted_offers" : fake.random_int( 0, 100 ),
                "canceled_offers" : fake.random_int( 0, 100 ),
                "average_reply_time" : fake.random_int( 1, 3600 ),
            }
            taxpayers.append( taxpayer )

        # Writing to taxpayers.json
        with open( os.path.join( os.path.dirname( __file__ ), "taxpayers.json" ) , "w" ) as outfile:
            json.dump( taxpayers, outfile )

    def distance_to_office( self, latitudes : float, longitudes : float, office_location: tuple  ) -> float: 
        return haversine( ( office_location[0], 
                            office_location[1] ),
                          ( latitudes,
                           longitudes)
                        )

    
    def calculate_scores( self, df:pd.DataFrame, office_location: tuple ) -> pd.DataFrame:
        # Calcular la distancia de cada cliente a la oficina
        df[ 'distance' ] = df.apply(
            lambda row: self.distance_to_office(
                row[ 'location.latitude' ], row[ 'location.longitude' ], office_location
            ), axis=1
        )
        

        # Normalization
        features = list( settings[ 'weights' ].keys() ) 
        scaler = MinMaxScaler()
        df[ features ] = scaler.fit_transform( df[ features ] )
        
        #score
        df[ 'score' ] = 0.0
        for feature, weight in settings[ 'weights' ].items():
            if feature in df.columns:
                df[ 'score' ] += df[ feature ] * weight
        df[ 'score' ] = df[ 'score' ] * 10 
        df[ 'score' ] = df[ 'score' ].clip(1, 10)

        #list client top
        top_clients = df.nlargest( settings[ 'num_client' ], 'score')

        # definition criterial
        low_data_criteria = (
            ( df[ 'accepted_offers' ] >= settings[ 'low_data_criteria' ][ 'accepted' ] ) &
            ( df[ 'canceled_offers' ] <= settings[ 'low_data_criteria' ][ 'canceled' ] ) &
            ( df[ 'average_reply_time' ] <= settings[ 'low_data_criteria' ][ 'time' ] )
        )
        # filter data
        low_data_clients = df[low_data_criteria]
        
        if not low_data_criteria.empty and settings[ 'num_remplace' ] > 0:
            clients_to_replace = top_clients.sample( int( settings[ 'num_remplace' ] ) )
            top_clients = top_clients.drop( clients_to_replace.index )
            low_data_sample = low_data_clients.sample( min( settings[ 'num_remplace' ],
                                                        len( low_data_clients ) )
                                                    )
            top_clients = pd.concat( [ top_clients, low_data_sample ] )

        top_clients = top_clients.nlargest( settings['num_client'], 'score')

        return top_clients[['id', 'name', 'score']].reset_index(drop=True)