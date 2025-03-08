import json
import os, sys
import base64
import tempfile
import git
from oauth2client.service_account import ServiceAccountCredentials

# This executes in AWS Lambda (copy it there)

def get_sheets_creds():
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
    if "sheets_creds_b64" in os.environ.keys():
        sheets_creds = base64.b64decode(os.environ["sheets_creds_b64"].encode("utf-8")).decode("utf-8")
    else:
        raise Exception("Missing sheets_creds in environment variables")
    return ServiceAccountCredentials.from_json_keyfile_dict(json.loads(sheets_creds, strict=False))
    
def get_aws_creds():
    if "access_key" in os.environ.keys():
        # Get locally exported creds in test mode
        return { 
            "access_key": os.environ["access_key"],
            "secret_key": os.environ["private_key"],
        }
    else:
        raise Exception("Missing access_key in environment variables")

def clone_repo():
    tmp_path = tempfile.mkdtemp()
    git_url = "https://github.com/michaelmu/lindabaird.git"
    git.Git(tmp_path).clone(git_url)
    return os.path.join(tmp_path, "lindabaird")

def lambda_handler(event, context):
    deploy = False if 'testmode' in event.keys() else True
    tmp_path = clone_repo()
    print("Temp path is: {}".format(tmp_path))
    sys.path.append(tmp_path)
    from build_site import SiteBuilder
    SiteBuilder(
        tmp_path, 
        aws_creds=get_aws_creds(),
        sheets_creds=get_sheets_creds(),
        ).update_site(deploy=deploy)
    
    return """
    !!Site refreshed!!
    
    Check it out at http://lindabairdmezzo.com
    """