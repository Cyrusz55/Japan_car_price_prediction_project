
from pydantic import BaseModel, Field
from typing import Literal, Optional


class JapanCarInput(BaseModel):
    vehicle_age: float = Field(..., description="Age of the vehicle in years")
    doors_num: float = Field(..., description="Number of doors")
    seats_num: float = Field(..., description="Number of seats")

    market_country: Literal[
        "Japan",
        "Mozambique",
        "Angola",
        "Burundi",
        "Chile",
        "Paraguay",
        "Guatemala",
        "Costa Rica",
        "Dominican Republic",
        "Russia",
        "Democratic Republic of the Congo",
        "Other",
    ] = Field(..., description="Market country inferred from the listing URL or title")

    stock_country: Literal[
        "Japan",
        "Singapore",
        "United Kingdom",
        "Australia",
        "Other",
    ] = Field(..., description="Country where the vehicle is stocked")

    is_overseas_stock: Literal[True, False] = Field(
        ..., description="Whether the stock is outside Japan"
    )

    make_clean: Literal[
        "TOYOTA",
        "NISSAN",
        "HONDA",
        "MAZDA",
        "MITSUBISHI",
        "SUZUKI",
        "SUBARU",
        "ISUZU",
        "DAIHATSU",
        "LEXUS",
        "AUDI",
        "BMW",
        "CHEVROLET",
        "FIAT",
        "FORD",
        "JAGUAR",
        "JEEP",
        "LAND ROVER",
        "MERCEDES-BENZ",
        "MINI",
        "PORSCHE",
        "RENAULT",
        "SMART",
        "TESLA",
        "VOLKSWAGEN",
        "VOLVO",
        "ALFA ROMEO",
        "AMG",
        "HINO",
        "PEUGEOT",
        "MASERATI",
        "Other",
    ] = Field(..., description="Cleaned vehicle make")

    model_clean: str = Field(..., description="Cleaned vehicle model")

    age_bucket: Literal["0-1", "2-3", "4-5", "6-10", "11-20", "20+"] = Field(
        ..., description="Age bucket of the vehicle"
    )

    fuel_group: Literal[
        "Electric",
        "Hybrid(Diesel)",
        "Hybrid(Petrol)",
        "Diesel",
        "Petrol",
        "Other",
    ] = Field(..., description="Grouped fuel type")

    transmission_group: Literal["CVT", "Manual", "Automatic", "Other"] = Field(
        ..., description="Grouped transmission type"
    )

    drive_group: Literal["4WD", "2WD", "Other"] = Field(
        ..., description="Grouped drive type"
    )

    steering_group: Literal["Right", "Left"] = Field(
        ..., description="Grouped steering side"
    )

    vin_region: Literal[
        "Japan",
        "Korea",
        "United Kingdom",
        "Germany",
        "USA",
        "Canada",
        "Mexico",
        "China",
        "France/Spain",
        "Italy",
        "Sweden/Finland",
        "Other",
    ] = Field(..., description="VIN region inferred from chassis number")

    body_guess: Literal[
        "truck_pickup",
        "van",
        "wagon",
        "convertible_roadster",
        "mpv_minivan",
        "coupe_roadster_like",
        "sedan_like",
        "suv_crossover_like",
        "unknown",
    ] = Field(..., description="Heuristic body-style classification")


class PredictionResponse(BaseModel):
    predicted_price: float = Field(..., description="Predicted price in original currency scale")
    status: str = "success"