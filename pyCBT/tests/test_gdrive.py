from pyCBT.providers.gdrive import account
from pyCBT.providers.gdrive import historical


client = account.Client()
historical.Table(name="adp-nonfarm-employment-change-1.csv").download()
