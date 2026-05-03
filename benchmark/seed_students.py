import csv
from concurrent.futures import ThreadPoolExecutor

import boto3

REGION = "us-east-1"
TABLE_NAME = "gr-grades-team07"
COURSE_CODE = "CLOUD101"
GRADE_ITEM = "midterm"
STUDENT_COUNT = 1500

ddb = boto3.resource("dynamodb", region_name=REGION)
table = ddb.Table(TABLE_NAME)


def write_student(index):
    student_id = f"S-{1000000 + index}"
    student_username = f"stu{index}"

    table.put_item(
        Item={
            "PK": f"COURSE#{COURSE_CODE}",
            "SK": f"STUDENT#{student_id}#GRADE#{GRADE_ITEM}",
            "course_code": COURSE_CODE,
            "student_id": student_id,
            "grade_item": GRADE_ITEM,
            "score": 70 + (index % 30),
            "student_username": student_username,
            "last_request_id": f"seed-{index}",
            "updated_at": "2026-05-03T00:00:00Z",
            "status_last": "stored"
        }
    )

    return student_id


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=32) as pool:
        student_ids = list(pool.map(write_student, range(STUDENT_COUNT)))

    with open("students.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["student_id"])
        for student_id in student_ids:
            writer.writerow([student_id])

    print(f"seeded {STUDENT_COUNT} students into {TABLE_NAME}")
    print("created students.csv")