import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import handlers


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def parse_body(event):
    raw_body = event.get("body")
    if not raw_body:
        return {}

    try:
        return json.loads(raw_body)
    except Exception:
        return None


def lambda_handler(event, context):
    request_context = event.get("requestContext") or {}
    http_info = request_context.get("http") or {}

    method = http_info.get("method") or event.get("httpMethod")
    raw_path = event.get("rawPath") or event.get("path") or ""
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    if method == "GET" and raw_path == "/health":
        status_code, body = handlers.health()
        return response(status_code, body)

    if method == "POST" and raw_path == "/grades":
        body = parse_body(event)
        if body is None:
            return response(400, {"error": "invalid_json_body"})
        status_code, response_body = handlers.post_grade(body)
        return response(status_code, response_body)

    if method == "GET" and raw_path.endswith("/grades") and "/students/" in raw_path:
        student_id = path_params.get("student_id")
        if not student_id:
            parts = raw_path.split("/")
            try:
                student_id = parts[2]
            except Exception:
                return response(400, {"error": "student_id missing"})

        course_code = query_params.get("course_code")
        status_code, body = handlers.get_student_grades(student_id, course_code)
        return response(status_code, body)

    if method == "POST" and raw_path.endswith("/finalize") and "/courses/" in raw_path:
        course_code = path_params.get("course_code")
        if not course_code:
            parts = raw_path.split("/")
            try:
                course_code = parts[2]
            except Exception:
                return response(400, {"error": "course_code missing"})

        body = parse_body(event)
        if body is None:
            return response(400, {"error": "invalid_json_body"})

        status_code, response_body = handlers.finalize_course(course_code, body)
        return response(status_code, response_body)

    return response(404, {"error": "route_not_found"})