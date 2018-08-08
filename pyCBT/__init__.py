import os

base_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_path, "data")
# TODO: check if data path exist. If not, create path
candles_header = "Datetime Open High Low Close Volume".split()
