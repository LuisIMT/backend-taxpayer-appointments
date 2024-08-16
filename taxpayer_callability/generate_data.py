###########################################################
#                                                         #
#   Sample data generation script                        #
#   Usage:                                                #
#     1. Install Faker library: pip3 install Faker        #
#     2. Run the script: python3 generate_data.py         #
#                                                         #
###########################################################

from faker import Faker
import json
import os
from haversine import haversine
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from config import settings

class gen_data:
    def __init__(self, seed) -> None:
        self.seed:int = seed

    def faker_data(self) -> None:

        fake = Faker()
        Faker.seed(self.seed)

        taxpayers = []

        for _ in range(1000):
            geolocation = fake.local_latlng(country_code="MX")
            taxpayer = {
                "id": fake.uuid4(),
                "name": fake.name(),
                "location": {
                "latitude":float(geolocation[0]),
                "longitude":float(geolocation[1])
                },
                "age" : fake.random_int(18, 90),
                "accepted_offers" : fake.random_int(0, 100),
                "canceled_offers" : fake.random_int(0, 100),
                "average_reply_time" : fake.random_int(1, 3600),
            }
            taxpayers.append(taxpayer)

        # Writing to taxpayers.json
        with open(os.path.join(os.path.dirname(__file__), "taxpayers.json"), "w") as outfile:
            json.dump(taxpayers, outfile)

    def distance_to_office( self, latitudes : float, longitudes : float ) -> float:
        #calculated distances 
        return haversine( ( settings[ 'office' ][ 'latitude' ], 
                           settings[ 'office' ][ 'longitude' ] ),
                          ( latitudes,
                           longitudes)
                        )

    
    def calculate_scores( self, df:pd.DataFrame) -> pd.DataFrame:
        # Calcular la distancia de cada cliente a la oficina
        df[ 'distance' ] = df.apply(
            lambda row: self.distance_to_office(
                row['location.latitude'], row['location.longitude']
            ), axis=1
        )

        # Seleccionar las características a normalizar
        features = ['age', 
                    'distance', 
                    'accepted_offers', 
                    'canceled_offers', 
                    'average_reply_time'
                    ]

        # Normalización Min-Max
        scaler = MinMaxScaler()
        df[ features ] = scaler.fit_transform( df[ features ] )

        # Calcular el puntaje final de cada cliente
        df['score'] = (
            df['age'] * settings[ 'weights' ][ 'age' ] +
            df['distance'] * settings[ 'weights' ][ 'distance' ] +
            df['accepted_offers'] * settings[ 'weights' ][ 'accepted_offers' ] +
            df['canceled_offers'] * settings[ 'weights' ][ 'canceled_offers' ] +
            df['average_reply_time'] *settings[ 'weights' ][ 'average_reply_time' ]
        ) * 10  # Escalar el resultado a un rango de 1 a 10

        # Limitar los puntajes al rango de 1 a 10
        df['score'] = df['score'].clip(1, 10)

        # Seleccionar los 10 clientes con el puntaje más alto
        top_clients = df.nlargest( settings['num_client'], 'score')

        # Definir criterios para considerar que un cliente tiene pocos datos de comportamiento
        df['low_data_criteria'] = ( df[ 'accepted_offers' ] <= settings['low_data_criteria']['accepted'] )\
                            & (df[ 'canceled_offers' ] <= settings['low_data_criteria']['canceled']   )\
                            & (df['average_reply_time'] <=  settings['low_data_criteria']['time'] 
                            )
        
        # Identificar clientes con pocos datos de comportamiento
        low_data_clients = df[df['low_data_criteria']]

        # Calcular el número de clientes a reemplazar (30% de num_clients)
        num_to_replace = int( settings['num_client'] * 0.30 )

        # Reemplazar aleatoriamente 30% de los clientes del top 10 con clientes de low_data_clients
        if not low_data_clients.empty and num_to_replace > 0:
            clients_to_replace = top_clients.sample(num_to_replace)
            low_data_sample = low_data_clients.sample(min(num_to_replace, len(low_data_clients)))

            # Reemplazar los clientes seleccionados
            top_clients = top_clients.drop(clients_to_replace.index)
            top_clients = pd.concat([top_clients, low_data_sample])

        # Asegurar que tenemos exactamente num_clients en la lista final
        top_clients = top_clients.nlargest( settings['num_client'], 'score')

    

        return top_clients[['id', 'name', 'score']].reset_index(drop=True)