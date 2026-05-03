from flask import Flask, jsonify, request

from . import handlers

app = Flask(__name__)


@app.get("/health")
def health():
    status_code, body = handlers.health()
    return jsonify(body), status_code


@app.post("/grades")
def post_grade():
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    status_code, response_body = handlers.post_grade(body)
    return jsonify(response_body), status_code


@app.get("/students/<student_id>/grades")
def get_student_grades(student_id):
    course_code = request.args.get("course_code")
    status_code, body = handlers.get_student_grades(student_id, course_code)
    return jsonify(body), status_code


@app.post("/courses/<course_code>/finalize")
def finalize_course(course_code):
    body = request.get_json(silent=True)
    if body is None:
        body = {}
    status_code, response_body = handlers.finalize_course(course_code, body)
    return jsonify(response_body), status_code