#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PAGE_REQUEST_FILTER = """
sc_status BETWEEN 200 AND 399
AND cs_method IN ('GET', 'HEAD')
AND cs_uri_stem NOT LIKE '/include/%'
AND cs_uri_stem NOT LIKE '/favicon.ico'
AND cs_uri_stem NOT LIKE '/robots.txt'
AND cs_uri_stem NOT LIKE '/sitemap%'
AND cs_uri_stem NOT LIKE '%.avif'
AND cs_uri_stem NOT LIKE '%.css'
AND cs_uri_stem NOT LIKE '%.eot'
AND cs_uri_stem NOT LIKE '%.gif'
AND cs_uri_stem NOT LIKE '%.ico'
AND cs_uri_stem NOT LIKE '%.jpeg'
AND cs_uri_stem NOT LIKE '%.jpg'
AND cs_uri_stem NOT LIKE '%.js'
AND cs_uri_stem NOT LIKE '%.json'
AND cs_uri_stem NOT LIKE '%.map'
AND cs_uri_stem NOT LIKE '%.mp4'
AND cs_uri_stem NOT LIKE '%.otf'
AND cs_uri_stem NOT LIKE '%.pdf'
AND cs_uri_stem NOT LIKE '%.png'
AND cs_uri_stem NOT LIKE '%.svg'
AND cs_uri_stem NOT LIKE '%.ttf'
AND cs_uri_stem NOT LIKE '%.txt'
AND cs_uri_stem NOT LIKE '%.webm'
AND cs_uri_stem NOT LIKE '%.webp'
AND cs_uri_stem NOT LIKE '%.woff'
AND cs_uri_stem NOT LIKE '%.woff2'
AND cs_uri_stem NOT LIKE '%.xml'
""".strip()

BOT_REGEX = "bot|crawl|spider|slurp|headless|lighthouse|wget|curl|python-requests"

DEVICE_CLASS_SQL = f"""
CASE
  WHEN regexp_like(user_agent, '{BOT_REGEX}') THEN 'Bots'
  WHEN regexp_like(user_agent, 'ipad|tablet|kindle|silk|playbook')
    OR (regexp_like(user_agent, 'android') AND NOT regexp_like(user_agent, 'mobile')) THEN 'Tablet'
  WHEN regexp_like(user_agent, 'iphone|ipod|windows phone|mobile')
    OR regexp_like(user_agent, 'android') THEN 'Mobile'
  WHEN user_agent = '' OR user_agent = '-' THEN 'Unknown'
  ELSE 'Desktop'
END
""".strip()

BROWSER_FAMILY_SQL = f"""
CASE
  WHEN regexp_like(user_agent, '{BOT_REGEX}') THEN 'Bots'
  WHEN regexp_like(user_agent, 'edg/|edge/') THEN 'Edge'
  WHEN regexp_like(user_agent, 'opr/|opera') THEN 'Opera'
  WHEN regexp_like(user_agent, 'samsungbrowser/') THEN 'Samsung Internet'
  WHEN regexp_like(user_agent, 'firefox/|fxios/') THEN 'Firefox'
  WHEN regexp_like(user_agent, 'chrome/|crios/') THEN 'Chrome'
  WHEN regexp_like(user_agent, 'safari/') THEN 'Safari'
  WHEN user_agent = '' OR user_agent = '-' THEN 'Unknown'
  ELSE 'Other'
END
""".strip()

OPERATING_SYSTEM_SQL = f"""
CASE
  WHEN regexp_like(user_agent, '{BOT_REGEX}') THEN 'Bots'
  WHEN regexp_like(user_agent, 'iphone|ipad|ipod|ios') THEN 'iOS'
  WHEN regexp_like(user_agent, 'android') THEN 'Android'
  WHEN regexp_like(user_agent, 'cros') THEN 'ChromeOS'
  WHEN regexp_like(user_agent, 'windows') THEN 'Windows'
  WHEN regexp_like(user_agent, 'mac os x|macintosh') THEN 'macOS'
  WHEN regexp_like(user_agent, 'linux') THEN 'Linux'
  WHEN user_agent = '' OR user_agent = '-' THEN 'Unknown'
  ELSE 'Other'
END
""".strip()

REFERRER_HOST_SQL = """
CASE
  WHEN referrer = '' OR referrer = '-' THEN 'Direct / Unknown'
  WHEN regexp_like(referrer, 'https?://(?:www\\.)?lindabairdmezzo\\.com(?:[:/]|$)')
    OR regexp_like(referrer, 'https?://michaelmu\\.github\\.io(?:[:/]|$)')
    OR regexp_like(referrer, 'https?://d2o8ggei9u5n44\\.cloudfront\\.net(?:[:/]|$)')
    OR regexp_like(referrer, 'https?://lindabairdmezzo\\.com\\.s3-website-us-west-1\\.amazonaws\\.com(?:[:/]|$)')
    THEN 'Internal navigation'
  WHEN regexp_extract(referrer, '^(?:https?://)?(?:www\\.)?([^/:?#]+)', 1) = '' THEN 'Other referrals'
  ELSE regexp_extract(referrer, '^(?:https?://)?(?:www\\.)?([^/:?#]+)', 1)
END
""".strip()


def run_aws(args: list[str], env: dict[str, str] | None = None) -> str:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        ["aws", *args],
        check=True,
        capture_output=True,
        text=True,
        env=full_env,
    )
    return result.stdout


def start_query(
    query: str,
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
) -> str:
    env = dict(**{"AWS_PROFILE": profile})
    stdout = run_aws(
        [
            "athena",
            "start-query-execution",
            "--work-group",
            workgroup,
            "--query-execution-context",
            f"Database={database}",
            "--result-configuration",
            f"OutputLocation={output_location}",
            "--query-string",
            query,
            "--query",
            "QueryExecutionId",
            "--output",
            "text",
        ],
        env=env,
    )
    return stdout.strip()


def wait_for_query(query_execution_id: str, *, profile: str) -> None:
    env = dict(**{"AWS_PROFILE": profile})
    while True:
        state = run_aws(
            [
                "athena",
                "get-query-execution",
                "--query-execution-id",
                query_execution_id,
                "--query",
                "QueryExecution.Status.State",
                "--output",
                "text",
            ],
            env=env,
        ).strip()
        if state == "SUCCEEDED":
            return
        if state in {"FAILED", "CANCELLED"}:
            reason = run_aws(
                [
                    "athena",
                    "get-query-execution",
                    "--query-execution-id",
                    query_execution_id,
                    "--query",
                    "QueryExecution.Status.StateChangeReason",
                    "--output",
                    "text",
                ],
                env=env,
            ).strip()
            raise RuntimeError(f"Athena query {query_execution_id} failed: {reason}")
        time.sleep(2)


def fetch_rows(query_execution_id: str, *, profile: str) -> list[dict[str, str]]:
    env = dict(**{"AWS_PROFILE": profile})
    stdout = run_aws(
        [
            "athena",
            "get-query-results",
            "--query-execution-id",
            query_execution_id,
            "--output",
            "json",
        ],
        env=env,
    )
    payload = json.loads(stdout)
    rows = payload["ResultSet"]["Rows"]
    if not rows:
        return []
    headers = [cell.get("VarCharValue", "") for cell in rows[0].get("Data", [])]
    parsed: list[dict[str, str]] = []
    for row in rows[1:]:
        values = [cell.get("VarCharValue", "") for cell in row.get("Data", [])]
        parsed.append(dict(zip(headers, values)))
    return parsed


def run_query(
    query: str,
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
) -> list[dict[str, str]]:
    query_execution_id = start_query(
        query,
        profile=profile,
        workgroup=workgroup,
        database=database,
        output_location=output_location,
    )
    wait_for_query(query_execution_id, profile=profile)
    return fetch_rows(query_execution_id, profile=profile)


def to_int(value: str) -> int:
    if value in {"", "NULL", None}:  # type: ignore[comparison-overlap]
        return 0
    return int(float(value))


def export_summary(*, profile: str, workgroup: str, database: str, output_location: str) -> dict:
    query = f"""
WITH page_requests AS (
  SELECT "date" AS log_date, c_ip, sc_bytes
  FROM cloudfront_standard_logs
  WHERE {PAGE_REQUEST_FILTER}
)
SELECT period, requests, unique_ip_count, bytes_served
FROM (
  SELECT
    'today' AS period,
    COUNT(*) AS requests,
    COUNT(DISTINCT c_ip) AS unique_ip_count,
    COALESCE(SUM(sc_bytes), 0) AS bytes_served
  FROM page_requests
  WHERE log_date = current_date

  UNION ALL

  SELECT
    'last_7_days' AS period,
    COUNT(*) AS requests,
    COUNT(DISTINCT c_ip) AS unique_ip_count,
    COALESCE(SUM(sc_bytes), 0) AS bytes_served
  FROM page_requests
  WHERE log_date >= current_date - interval '7' day

  UNION ALL

  SELECT
    'last_30_days' AS period,
    COUNT(*) AS requests,
    COUNT(DISTINCT c_ip) AS unique_ip_count,
    COALESCE(SUM(sc_bytes), 0) AS bytes_served
  FROM page_requests
  WHERE log_date >= current_date - interval '30' day
)
ORDER BY CASE period
  WHEN 'today' THEN 1
  WHEN 'last_7_days' THEN 2
  WHEN 'last_30_days' THEN 3
  ELSE 99
END
"""
    rows = run_query(
        query,
        profile=profile,
        workgroup=workgroup,
        database=database,
        output_location=output_location,
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "period": row["period"],
                "label": row["period"].replace("_", " ").title(),
                "requests": to_int(row["requests"]),
                "unique_ip_count": to_int(row["unique_ip_count"]),
                "bytes_served": to_int(row["bytes_served"]),
            }
            for row in rows
        ],
    }


def export_daily(
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
    days: int,
) -> dict:
    query = f"""
WITH page_requests AS (
  SELECT "date" AS log_date, c_ip, sc_bytes
  FROM cloudfront_standard_logs
  WHERE {PAGE_REQUEST_FILTER}
)
SELECT
  CAST(log_date AS VARCHAR) AS date,
  COUNT(*) AS requests,
  COUNT(DISTINCT c_ip) AS unique_ip_count,
  COALESCE(SUM(sc_bytes), 0) AS bytes_served
FROM page_requests
WHERE log_date >= current_date - interval '{days}' day
GROUP BY 1
ORDER BY 1 ASC
"""
    rows = run_query(
        query,
        profile=profile,
        workgroup=workgroup,
        database=database,
        output_location=output_location,
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "days": [
            {
                "date": row["date"],
                "requests": to_int(row["requests"]),
                "unique_ip_count": to_int(row["unique_ip_count"]),
                "bytes_served": to_int(row["bytes_served"]),
            }
            for row in rows
        ],
    }


def export_top_pages(
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
    days: int,
    limit: int,
) -> dict:
    query = f"""
SELECT
  CASE
    WHEN cs_uri_stem = '' THEN '/'
    ELSE cs_uri_stem
  END AS path,
  COUNT(*) AS requests
FROM cloudfront_standard_logs
WHERE "date" >= current_date - interval '{days}' day
  AND {PAGE_REQUEST_FILTER}
GROUP BY 1
ORDER BY requests DESC, path ASC
LIMIT {limit}
"""
    rows = run_query(
        query,
        profile=profile,
        workgroup=workgroup,
        database=database,
        output_location=output_location,
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "pages": [
            {
                "path": row["path"] or "/",
                "requests": to_int(row["requests"]),
            }
            for row in rows
        ],
    }


def export_dimension_breakdown(
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
    days: int,
    label_sql: str,
    limit: int | None = None,
) -> list[dict]:
    limit_clause = f"\nLIMIT {limit}" if limit else ""
    query = f"""
WITH page_requests AS (
  SELECT
    "date" AS log_date,
    c_ip,
    sc_bytes,
    lower(coalesce(cs_user_agent, '')) AS user_agent,
    lower(coalesce(cs_referrer, '')) AS referrer
  FROM cloudfront_standard_logs
  WHERE {PAGE_REQUEST_FILTER}
)
SELECT
  label,
  COUNT(*) AS requests,
  COUNT(DISTINCT c_ip) AS unique_ip_count
FROM (
  SELECT
    c_ip,
    {label_sql} AS label
  FROM page_requests
  WHERE log_date >= current_date - interval '{days}' day
) ranked
GROUP BY 1
ORDER BY requests DESC, unique_ip_count DESC, label ASC{limit_clause}
"""
    rows = run_query(
        query,
        profile=profile,
        workgroup=workgroup,
        database=database,
        output_location=output_location,
    )
    return [
        {
            "label": row["label"],
            "requests": to_int(row["requests"]),
            "unique_ip_count": to_int(row["unique_ip_count"]),
        }
        for row in rows
    ]


def export_segments(
    *,
    profile: str,
    workgroup: str,
    database: str,
    output_location: str,
    days: int,
    referrer_limit: int,
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": days,
        "device_types": export_dimension_breakdown(
            profile=profile,
            workgroup=workgroup,
            database=database,
            output_location=output_location,
            days=days,
            label_sql=DEVICE_CLASS_SQL,
        ),
        "browsers": export_dimension_breakdown(
            profile=profile,
            workgroup=workgroup,
            database=database,
            output_location=output_location,
            days=days,
            label_sql=BROWSER_FAMILY_SQL,
        ),
        "operating_systems": export_dimension_breakdown(
            profile=profile,
            workgroup=workgroup,
            database=database,
            output_location=output_location,
            days=days,
            label_sql=OPERATING_SYSTEM_SQL,
        ),
        "referrers": export_dimension_breakdown(
            profile=profile,
            workgroup=workgroup,
            database=database,
            output_location=output_location,
            days=days,
            label_sql=REFERRER_HOST_SQL,
            limit=referrer_limit,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="lindabairdmezzo-admin")
    parser.add_argument("--workgroup", default="lindabairdmezzo-analytics")
    parser.add_argument("--database", default="lindabairdmezzo_analytics")
    parser.add_argument(
        "--output-location",
        default="s3://lindabairdmezzo-com-cloudfront-logs-573542636309/athena-results/",
    )
    parser.add_argument("--output-dir", default="content/analytics")
    parser.add_argument("--daily-days", type=int, default=180)
    parser.add_argument("--top-days", type=int, default=30)
    parser.add_argument("--top-limit", type=int, default=12)
    parser.add_argument("--segment-days", type=int, default=30)
    parser.add_argument("--referrer-limit", type=int, default=8)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = export_summary(
        profile=args.profile,
        workgroup=args.workgroup,
        database=args.database,
        output_location=args.output_location,
    )
    daily = export_daily(
        profile=args.profile,
        workgroup=args.workgroup,
        database=args.database,
        output_location=args.output_location,
        days=args.daily_days,
    )
    top_pages = export_top_pages(
        profile=args.profile,
        workgroup=args.workgroup,
        database=args.database,
        output_location=args.output_location,
        days=args.top_days,
        limit=args.top_limit,
    )
    segments = export_segments(
        profile=args.profile,
        workgroup=args.workgroup,
        database=args.database,
        output_location=args.output_location,
        days=args.segment_days,
        referrer_limit=args.referrer_limit,
    )

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (output_dir / "daily.json").write_text(json.dumps(daily, indent=2) + "\n", encoding="utf-8")
    (output_dir / "top-pages.json").write_text(json.dumps(top_pages, indent=2) + "\n", encoding="utf-8")
    (output_dir / "segments.json").write_text(json.dumps(segments, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {output_dir / 'summary.json'}")
    print(f"Wrote {output_dir / 'daily.json'}")
    print(f"Wrote {output_dir / 'top-pages.json'}")
    print(f"Wrote {output_dir / 'segments.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
