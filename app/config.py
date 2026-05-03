import os

TEAM_ID = os.environ.get("TEAM_ID", "team-07")
CHALLENGE_CODE = os.environ.get("CHALLENGE_CODE", "K7Q3")
TEAM_MEMBERS = os.environ.get("TEAM_MEMBERS", "tuccaro,ertugrule,kadiogluu").split(",")

STAGE = os.environ.get("STAGE", "stage3")

DDB_TABLE = os.environ.get("DDB_TABLE", "gr-grades-team07")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")