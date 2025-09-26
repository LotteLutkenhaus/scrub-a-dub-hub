from google.cloud import secretmanager

PROJECT_ID = "java-janitor"


def get_secret(token_name: str) -> str:
    """
    Gets the secret from Google Secret Manager
    :param token_name: str with name of the token in GSM
    :return: secret: str unhashed version of the secret
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{token_name}/versions/latest"
    response = client.access_secret_version(name=name)
    secret = response.payload.data.decode("UTF-8")

    assert isinstance(secret, str)

    return secret
