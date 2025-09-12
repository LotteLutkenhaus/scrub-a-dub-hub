from google.cloud import secretmanager

PROJECT_ID = "java-janitor"

def get_secret(token_name):
    """
    Gets the secret from Google Secret Manager
    :param token_name: str with name of the token in GSM
    :return: secret: str unhashed version of the secret
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{token_name}/versions/latest"
    response = client.access_secret_version(name=name)
    secret = response.payload.data.decode("UTF-8")

    return secret


def add_secret_version(token_name, payload):
    """
    Add a new secret version to the given secret with the provided payload.
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the parent secret.
    parent = client.secret_path(PROJECT_ID, token_name)

    # Convert the string payload into a bytes. This step can be omitted if you
    # pass in bytes instead of a str for the payload argument.
    payload = payload.encode("UTF-8")

    # Add the secret version.
    client.add_secret_version(request={"parent": parent, "payload": {"data": payload}})