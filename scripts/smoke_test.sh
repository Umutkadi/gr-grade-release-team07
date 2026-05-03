#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-}"
COURSE="${2:-CLOUD900}"
STUDENT_ID="${3:-S-900001}"
STUDENT_USERNAME="${4:-demo-user}"

if [ -z "$BASE" ]; then
  echo "Usage: ./scripts/smoke_test.sh <BASE_URL> [COURSE] [STUDENT_ID] [STUDENT_USERNAME]"
  echo
  echo "Example:"
  echo "./scripts/smoke_test.sh http://3.80.10.20 CLOUD901 S-901001 stage1-user"
  echo "./scripts/smoke_test.sh http://stage2-alb.us-east-1.elb.amazonaws.com CLOUD902 S-902001 stage2-user"
  echo "./scripts/smoke_test.sh https://abc123.execute-api.us-east-1.amazonaws.com CLOUD903 S-903001 stage3-user"
  exit 1
fi

echo "====================================================="
echo "Grade Release Smoke Test"
echo "BASE=$BASE"
echo "COURSE=$COURSE"
echo "STUDENT_ID=$STUDENT_ID"
echo "STUDENT_USERNAME=$STUDENT_USERNAME"
echo "====================================================="

echo
echo "1) GET /health"
curl -s "$BASE/health" | python3 -m json.tool

echo
echo "2) POST /grades — stored"
curl -s -X POST "$BASE/grades" \
  -H "Content-Type: application/json" \
  -d "{\"course_code\":\"$COURSE\",\"grade_item\":\"midterm\",\"student_id\":\"$STUDENT_ID\",\"student_username\":\"$STUDENT_USERNAME\",\"score\":75,\"request_id\":\"smoke-$COURSE-1\"}" \
  | python3 -m json.tool

echo
echo "3) POST /grades — same request_id idempotency"
curl -s -X POST "$BASE/grades" \
  -H "Content-Type: application/json" \
  -d "{\"course_code\":\"$COURSE\",\"grade_item\":\"midterm\",\"student_id\":\"$STUDENT_ID\",\"student_username\":\"$STUDENT_USERNAME\",\"score\":75,\"request_id\":\"smoke-$COURSE-1\"}" \
  | python3 -m json.tool

echo
echo "4) POST /grades — same logical key, different request_id, update"
curl -s -X POST "$BASE/grades" \
  -H "Content-Type: application/json" \
  -d "{\"course_code\":\"$COURSE\",\"grade_item\":\"midterm\",\"student_id\":\"$STUDENT_ID\",\"student_username\":\"$STUDENT_USERNAME\",\"score\":80,\"request_id\":\"smoke-$COURSE-2\"}" \
  | python3 -m json.tool

echo
echo "5) GET /students/{student_id}/grades"
curl -s "$BASE/students/$STUDENT_ID/grades?course_code=$COURSE" | python3 -m json.tool

echo
echo "6) POST /courses/{course_code}/finalize"
curl -s -X POST "$BASE/courses/$COURSE/finalize" \
  -H "Content-Type: application/json" \
  -d "{\"request_id\":\"fin-$COURSE-1\",\"notify\":true}" \
  | python3 -m json.tool

echo
echo "7) POST /grades after finalize — must return 409"
curl -s -i -X POST "$BASE/grades" \
  -H "Content-Type: application/json" \
  -d "{\"course_code\":\"$COURSE\",\"grade_item\":\"final\",\"student_id\":\"$STUDENT_ID\",\"student_username\":\"$STUDENT_USERNAME\",\"score\":90,\"request_id\":\"smoke-$COURSE-3\"}"

echo
echo
echo "8) Re-finalize different request_id — should return already_finalized"
curl -s -X POST "$BASE/courses/$COURSE/finalize" \
  -H "Content-Type: application/json" \
  -d "{\"request_id\":\"fin-$COURSE-2\",\"notify\":true}" \
  | python3 -m json.tool

echo
echo "====================================================="
echo "Smoke test finished"
echo "====================================================="
