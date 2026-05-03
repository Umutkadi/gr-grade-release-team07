import http from "k6/http";
import { check } from "k6";
import { SharedArray } from "k6/data";
import exec from "k6/execution";
import papaparse from "https://jslib.k6.io/papaparse/5.1.1/index.js";

const STUDENTS = new SharedArray("students", function () {
  const file = open(__ENV.STUDENT_FILE || "students.csv");
  return papaparse.parse(file, { header: true }).data
    .map((row) => row.student_id)
    .filter(Boolean);
});

export const options = {
  discardResponseBodies: false,
  scenarios: {
    baseline: {
      executor: "constant-arrival-rate",
      rate: 300,
      timeUnit: "1m",
      duration: "5m",
      preAllocatedVUs: 120,
      maxVUs: 300
    },
    rampup: {
      executor: "ramping-arrival-rate",
      startRate: 300,
      timeUnit: "1m",
      preAllocatedVUs: 120,
      maxVUs: 300,
      startTime: "5m",
      stages: [
        { duration: "2m", target: 450 },
        { duration: "2m", target: 600 },
        { duration: "2m", target: 750 },
        { duration: "2m", target: 900 },
        { duration: "2m", target: 900 }
      ]
    },
    burst: {
      executor: "constant-arrival-rate",
      rate: 1650,
      timeUnit: "1m",
      duration: "7m",
      preAllocatedVUs: 120,
      maxVUs: 300,
      startTime: "15m"
    },
    recovery: {
      executor: "ramping-arrival-rate",
      startRate: 1650,
      timeUnit: "1m",
      preAllocatedVUs: 120,
      maxVUs: 300,
      startTime: "22m",
      stages: [
        { duration: "2m", target: 900 },
        { duration: "2m", target: 600 },
        { duration: "2m", target: 300 },
        { duration: "2m", target: 300 }
      ]
    }
  }
};

const BASE_URL = __ENV.BASE_URL;
const COURSE_CODE = __ENV.COURSE_CODE || "CLOUD101";

export default function () {
  const index = exec.scenario.iterationInTest % STUDENTS.length;
  const studentId = STUDENTS[index];

  const response = http.get(
    `${BASE_URL}/students/${studentId}/grades?course_code=${COURSE_CODE}`
  );

  check(response, {
    "status is 200": (r) => r.status === 200,
    "response has grades": (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.grades);
      } catch (e) {
        return false;
      }
    }
  });
}