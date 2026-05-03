# Grade Release System — Team 07

## Repository

Kaynak kod GitHub: https://github.com/Umutkadi/gr-grade-release-team07

## Team

- Ömer Tüccar (`tuccaro`) — Stage 1 Single EC2
- Enes Ertuğrul (`ertugrule`) — Stage 2 ALB + Auto Scaling
- Umut Kadıoğlu (`kadiogluu`) — Stage 3 Serverless

## Shared AWS Resources

- DynamoDB: `gr-grades-team07`
- SNS: `gr-grade-released-team07`
- EC2 role: `gr-ec2-instance-role-team07`
- Lambda role: `gr-lambda-exec-role-team07`

## Folder Structure

```text
app/
  Shared backend logic for all stages

lambda_pkg/
  Lambda router for Stage 3

benchmark/
  k6 scripts and seed script

docs/
  API contract and shared notes
```

## Stages

### Stage 1

Runs `app.main:app` on a single EC2 instance with Gunicorn.

### Stage 2

Runs `app.main:app` on EC2 instances behind ALB and Auto Scaling Group.

### Stage 3

Runs `lambda_pkg/handler.py` as a Lambda router behind API Gateway HTTP API.
