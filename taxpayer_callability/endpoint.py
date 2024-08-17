from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json, os
import pandas as pd
from generate_data import gen_data
from config import settings

app = FastAPI()

# Define el modelo de datos para la ubicación de la oficina
class OfficeLocation( BaseModel ):
    latitude : float
    longitude : float

# Define el modelo de datos para la respuesta
class Client( BaseModel ):
    id: str
    name: str
    score: float

@app.get( "/" )
def read_root():
    return { "message" : "Welcome to the FastAPI application" }


@app.post( "/list-client/" , response_model=list[ Client ] )
async def post_top_clients( office_location: OfficeLocation ):

    data = gen_data(seed=0)
    data.faker_data()

    with open( os.path.join( os.path.dirname( __file__ ), "taxpayers.json" ) ) as f:
        df = json.load( f )
    dataset = pd.json_normalize( df )

    list_client = data.calculate_scores(
        df=dataset,
        office_location = ( office_location.latitude, office_location.longitude )
    )

    return list_client.to_dict( orient='records' )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run( app, host="0.0.0.0", port=8000 )
