import io
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from pyCBT.common.path import exist


def get_client():
	if not exist("client_secrets.json"):
		with open("client_secrets.json", "w") as file_secret:
			file_secret.write(u"""{"installed":{"client_id":"693473631117-r01f6cl8lenbrrvpr2k2ouvh1qnpq49t.apps.googleusercontent.com","project_id":"norse-coral-205207","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"yEckBRaFUhdK2HQMWU009Stg","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}\n""")
			file_secret.close()

	gauth = GoogleAuth()
	gauth.LocalWebserverAuth()
	client = GoogleDrive(gauth)
	return client
