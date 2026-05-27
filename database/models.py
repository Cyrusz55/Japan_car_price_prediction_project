from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CleanedJapanCars(Base):
    __tablename__ = 'cleaned_japan_cars'

    id = Column(Integer, primary_key=True, autoincrement=True)

    vehicle_age = Column(Float, nullable=True)
    doors_num = Column(Float, nullable=True)
    seats_num = Column(Float, nullable=True)

    market_country = Column(String, nullable=True)
    stock_country = Column(String, nullable=True)
    is_overseas_stock = Column(Boolean, nullable=True)

    make_clean = Column(String, nullable=True)
    model_clean = Column(String, nullable=True)
    age_bucket = Column(String, nullable=True)
    fuel_group = Column(String, nullable=True)
    transmission_group = Column(String, nullable=True)
    drive_group = Column(String, nullable=True)
    steering_group = Column(String, nullable=True)
    vin_region = Column(String, nullable=True)
    body_guess = Column(String, nullable=True)

    # target column
    price_log = Column(Float, nullable=True)

def create_tables(engine):
    Base.metadata.create_all(engine)
    print("[db] Tables created")