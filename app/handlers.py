from datetime import datetime, timezone

from . import config, storage, notify


def identity_fields():
    return {
        "team_id": config.TEAM_ID,
        "challenge_code": config.CHALLENGE_CODE
    }


def health():
    return 200, {
        "ok": True,
        "stage": config.STAGE,
        "team_id": config.TEAM_ID,
        "team_members": config.TEAM_MEMBERS,
        "challenge_code": config.CHALLENGE_CODE,
        "ts_utc": datetime.now(timezone.utc).isoformat()
    }


def post_grade(body):
    if not isinstance(body, dict):
        return 400, {
            "error": "invalid_json_body",
            **identity_fields()
        }

    required_fields = [
        "course_code",
        "grade_item",
        "student_id",
        "score",
        "request_id"
    ]

    for field in required_fields:
        if field not in body or body[field] in [None, ""]:
            return 400, {
                "error": f"missing field: {field}",
                **identity_fields()
            }

    request_id = str(body["request_id"])

    cached = storage.get_idempotent(request_id)
    if cached:
        return cached["status_code"], cached["body"]

    try:
        score = int(body["score"])
    except (TypeError, ValueError):
        response = {
            "error": "score must be integer 0-100",
            **identity_fields()
        }
        storage.save_idempotent(request_id, "post_grade", 400, response)
        return 400, response

    if score < 0 or score > 100:
        response = {
            "error": "score out of range 0-100",
            **identity_fields()
        }
        storage.save_idempotent(request_id, "post_grade", 400, response)
        return 400, response

    course_code = str(body["course_code"])
    grade_item = str(body["grade_item"])
    student_id = str(body["student_id"])
    student_username = body.get("student_username")

    meta = storage.get_course_meta(course_code)
    if meta and meta.get("finalized"):
        response = {
            "error": "course already finalized",
            "status": "rejected",
            **identity_fields()
        }
        storage.save_idempotent(request_id, "post_grade", 409, response)
        return 409, response

    status = storage.upsert_grade(
        course_code=course_code,
        student_id=student_id,
        grade_item=grade_item,
        score=score,
        student_username=student_username,
        request_id=request_id
    )

    response = {
        "status": status,
        "course_code": course_code,
        "grade_item": grade_item,
        "student_id": student_id,
        "student_username": student_username,
        "request_id": request_id,
        **identity_fields()
    }

    storage.save_idempotent(request_id, "post_grade", 200, response)
    return 200, response


def get_student_grades(student_id, course_code):
    if not course_code:
        return 400, {
            "error": "course_code query param required",
            **identity_fields()
        }

    items = storage.query_student_grades(course_code, student_id)

    grades = []
    student_username = None

    for item in items:
        grade_item = item.get("grade_item")
        if not grade_item:
            grade_item = item["SK"].split("#GRADE#")[-1]

        grades.append({
            "grade_item": grade_item,
            "score": int(item["score"])
        })

        if item.get("student_username"):
            student_username = item["student_username"]

    return 200, {
        "student_id": student_id,
        "student_username": student_username,
        "course_code": course_code,
        "grades": grades,
        **identity_fields()
    }


def finalize_course(course_code, body):
    if not isinstance(body, dict):
        return 400, {
            "error": "invalid_json_body",
            **identity_fields()
        }

    if "request_id" not in body or body["request_id"] in [None, ""]:
        return 400, {
            "error": "request_id required",
            **identity_fields()
        }

    request_id = str(body["request_id"])

    cached = storage.get_idempotent(request_id)
    if cached:
        return cached["status_code"], cached["body"]

    meta = storage.get_course_meta(course_code)

    if meta and meta.get("finalized"):
        response = {
            "status": "already_finalized",
            "course_code": course_code,
            "request_id": request_id,
            "notification_mode": "sns-publish-only",
            **identity_fields()
        }
        storage.save_idempotent(request_id, "finalize", 200, response)
        return 200, response

    finalize_result = storage.mark_course_finalized(course_code, request_id)

    if finalize_result == "already_finalized":
        response = {
            "status": "already_finalized",
            "course_code": course_code,
            "request_id": request_id,
            "notification_mode": "sns-publish-only",
            **identity_fields()
        }
        storage.save_idempotent(request_id, "finalize", 200, response)
        return 200, response

    if body.get("notify", True):
        message_id = notify.publish_release(course_code, request_id)
        storage.mark_notification_published(course_code, message_id)

    response = {
        "status": "finalized",
        "course_code": course_code,
        "request_id": request_id,
        "notification_mode": "sns-publish-only",
        **identity_fields()
    }

    storage.save_idempotent(request_id, "finalize", 200, response)
    return 200, response