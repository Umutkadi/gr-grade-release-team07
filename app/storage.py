import json
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import config

_ddb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
_table = _ddb.Table(config.DDB_TABLE)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_idempotent(request_id):
    """
    Returns:
      None if request_id was not seen before
      {"status_code": int, "body": dict} if cached response exists
    """
    result = _table.get_item(
        Key={
            "PK": f"REQ#{request_id}",
            "SK": f"REQ#{request_id}"
        }
    )
    item = result.get("Item")
    if not item:
        return None

    return {
        "status_code": int(item.get("status_code", 200)),
        "body": json.loads(item["response_json"])
    }


def save_idempotent(request_id, op, status_code, response_body):
    ttl_value = int(datetime.now(timezone.utc).timestamp()) + 86400

    _table.put_item(
        Item={
            "PK": f"REQ#{request_id}",
            "SK": f"REQ#{request_id}",
            "op": op,
            "status_code": int(status_code),
            "response_json": json.dumps(response_body),
            "ttl": ttl_value,
            "created_at": utc_now()
        }
    )


def get_course_meta(course_code):
    result = _table.get_item(
        Key={
            "PK": f"COURSE#{course_code}",
            "SK": "META"
        }
    )
    return result.get("Item")


def mark_course_finalized(course_code, request_id):
    """
    Marks a course as finalized if it was not finalized before.

    Returns:
      "finalized" if this request finalized the course
      "already_finalized" if course was already finalized
    """
    try:
        _table.update_item(
            Key={
                "PK": f"COURSE#{course_code}",
                "SK": "META"
            },
            UpdateExpression=(
                "SET finalized = :true_value, "
                "finalize_request_id = :request_id, "
                "finalized_at = :finalized_at, "
                "notification_published = :false_value"
            ),
            ConditionExpression="attribute_not_exists(finalized) OR finalized = :false_value",
            ExpressionAttributeValues={
                ":true_value": True,
                ":false_value": False,
                ":request_id": request_id,
                ":finalized_at": utc_now()
            }
        )
        return "finalized"

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return "already_finalized"
        raise


def mark_notification_published(course_code, message_id=None):
    update_expression = "SET notification_published = :true_value"
    values = {
        ":true_value": True
    }

    if message_id:
        update_expression += ", notification_message_id = :message_id"
        values[":message_id"] = message_id

    _table.update_item(
        Key={
            "PK": f"COURSE#{course_code}",
            "SK": "META"
        },
        UpdateExpression=update_expression,
        ExpressionAttributeValues=values
    )


def upsert_grade(course_code, student_id, grade_item, score, student_username, request_id):
    pk = f"COURSE#{course_code}"
    sk = f"STUDENT#{student_id}#GRADE#{grade_item}"

    existing = _table.get_item(
        Key={
            "PK": pk,
            "SK": sk
        }
    ).get("Item")

    status = "stored" if existing is None else "updated"

    item = {
        "PK": pk,
        "SK": sk,
        "course_code": course_code,
        "student_id": student_id,
        "grade_item": grade_item,
        "score": int(score),
        "student_username": student_username or "",
        "last_request_id": request_id,
        "updated_at": utc_now(),
        "status_last": status
    }

    _table.put_item(Item=item)
    return status


def query_student_grades(course_code, student_id):
    pk = f"COURSE#{course_code}"
    prefix = f"STUDENT#{student_id}#GRADE#"

    result = _table.query(
        KeyConditionExpression=Key("PK").eq(pk) & Key("SK").begins_with(prefix)
    )

    return result.get("Items", [])