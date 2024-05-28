import os
import json
from cryptography.fernet import Fernet

# Retrieve encryption key from environment variable
key_str = os.getenv('TEST_CASE_CREATION_SECRET_KEY')
if not key_str:
    raise EnvironmentError('TEST_CASE_CREATION_SECRET_KEY environment variable not found.')
key = key_str.encode()

fernet = Fernet(key)

def encrypt_file(input_filepath, output_filepath):
    """
    Encrypts the content of a json file and writes it to an output file.
    """
    # Read the content from the input file
    with open(input_filepath, 'r') as f:
        data = json.load(f)

    # Serialize and encrypt the data
    json_data = json.dumps(data).encode()
    encrypted_data = fernet.encrypt(json_data)
    
    # Write the encrypted data to the output file
    with open(output_filepath, 'wb') as f:
        f.write(encrypted_data)

def decrypt_file(input_filepath):
    """
    Decrypts the content of an encrypted file and writes the decrypted data as json.
    """
    # Read the encrypted data from the input file
    with open(input_filepath, 'rb') as f:
        encrypted_data = f.read()

    # Decrypt and deserialize the data
    decrypted_data = fernet.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

##encrypt_file('slack_google_credentials.json', 'slack_google_credentials.enc')