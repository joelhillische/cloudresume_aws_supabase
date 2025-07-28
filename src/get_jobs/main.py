import requests
import boto3
from supabase import create_client

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Silence noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Load AWS SSM client
ssm = boto3.client("ssm")

def get_ssm_param(name, decrypt=True):
    return ssm.get_parameter(Name=name, WithDecryption=decrypt)['Parameter']['Value']

# Load environment variables and secrets
SUPABASE_TABLE = os.environ["SUPABASE_TABLE"]
SUPABASE_URL = get_ssm_param(os.environ["SUPABASE_URL_SSM_PATH"])
SUPABASE_KEY = get_ssm_param(os.environ["SUPABASE_KEY_SSM_PATH"])
EXTERNAL_API_URL = get_ssm_param(os.environ["EXTERNAL_API_URL"])
EXTERNAL_API_KEY = get_ssm_param(os.environ["EXTERNAL_API_KEY_SSM_PATH"])

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_external_data():
    headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
    response = requests.get(EXTERNAL_API_URL, headers=headers)
    response.raise_for_status()
    return response.json()  # Expecting a list of user records or similar

def lambda_handler(event, context):
    try:
        data = fetch_external_data()
        logger.info(f"Fetched {len(data)} record(s) from external API.")
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return {"status": "error", "message": str(e)}

    for record in data:
        # Customize as needed; assumes each `record` is already a dict
        supabase.table(SUPABASE_TABLE).upsert(record).execute()

    return {"status": "success", "inserted_records": len(data)}
