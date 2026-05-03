import json

import boto3

from . import config

_sns = boto3.client("sns", region_name=config.AWS_REGION)


def publish_release(course_code, request_id):
    if not config.SNS_TOPIC_ARN:
        return None

    response = _sns.publish(
        TopicArn=config.SNS_TOPIC_ARN,
        Subject=f"GradeRelease {course_code}",
        Message=json.dumps({
            "event": "course-finalized",
            "course_code": course_code,
            "request_id": request_id,
            "team_id": config.TEAM_ID,
            "challenge_code": config.CHALLENGE_CODE
        })
    )

    return response.get("MessageId")