# Grade Release API Contract

## Identity

Every response must include:

```json
{
  "team_id": "team-07",
  "challenge_code": "K7Q3"
}
```

`GET /health` must also include:

```json
{
  "team_members": ["tuccaro", "ertugrule", "kadiogluu"]
}
```

---

## 1. GET /health

Response:

```json
{
  "ok": true,
  "stage": "stage1|stage2|stage3",
  "team_id": "team-07",
  "team_members": ["tuccaro", "ertugrule", "kadiogluu"],
  "challenge_code": "K7Q3",
  "ts_utc": "..."
}
```

---

## 2. POST /grades

Request:

```json
{
  "course_code": "CLOUD101",
  "grade_item": "midterm",
  "student_id": "S-100045",
  "student_username": "jdoe",
  "score": 85,
  "request_id": "unique-request-id"
}
```

Response:

```json
{
  "status": "stored|updated",
  "course_code": "CLOUD101",
  "grade_item": "midterm",
  "student_id": "S-100045",
  "student_username": "jdoe",
  "request_id": "unique-request-id",
  "team_id": "team-07",
  "challenge_code": "K7Q3"
}
```

Rules:

- `request_id` is required.
- `score` must be between 0 and 100.
- If the course is finalized, this endpoint must return 409.
- Same request_id must return the cached response.

---

## 3. GET /students/{student_id}/grades?course_code=CLOUD101

Response:

```json
{
  "student_id": "S-100045",
  "student_username": "jdoe",
  "course_code": "CLOUD101",
  "grades": [
    {
      "grade_item": "midterm",
      "score": 85
    }
  ],
  "team_id": "team-07",
  "challenge_code": "K7Q3"
}
```

---

## 4. POST /courses/{course_code}/finalize

Request:

```json
{
  "request_id": "unique-request-id",
  "notify": true
}
```

Response:

```json
{
  "status": "finalized|already_finalized",
  "course_code": "CLOUD101",
  "request_id": "unique-request-id",
  "notification_mode": "sns-publish-only",
  "team_id": "team-07",
  "challenge_code": "K7Q3"
}
```

Rules:

- Finalize must be idempotent.
- SNS publish must happen at most once per course release.
- Real email/SMS is not required.
