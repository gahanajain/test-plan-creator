import time
import hmac
import hashlib

def verify_slack_signature(request_body, timestamp, signature, slack_signing_secret):
    """
    Verifies the Slack request's signature.
    
    Args:
        request_body (str): The body of the request from Slack.
        timestamp (str): The 'X-Slack-Request-Timestamp' header from the Slack request.
        signature (str): The 'X-Slack-Signature' header from the Slack request.
        slack_signing_secret (str): Your application's Slack signing secret.
    
    Returns:
        bool: True if verified, False if not.
    """
    # Slack recommends a time verification to protect against replay attacks
    # The difference in time should not exceed 5 minutes (60 * 5 seconds)
    if abs(time.time() - int(timestamp)) > 300:
        return False

    # Construct the signature base string
    sig_basestring = 'v0:' + timestamp + ':' + request_body
    
    # Create a new HMAC "signature", and return the hexadecimal digest
    my_signature = 'v0=' + hmac.new(
        str.encode(slack_signing_secret),
        str.encode(sig_basestring),
        hashlib.sha256
    ).hexdigest()
    
    # Compare the signatures using a timing attack resistant function
    if hmac.compare_digest(my_signature, signature):
        return True
    else:
        return False
