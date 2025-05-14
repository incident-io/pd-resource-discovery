import argparse
import requests
import csv
import os
from datetime import datetime

BASE_URL = "https://api.pagerduty.com"
API_HEADERS_TEMPLATE = {
    "Accept": "application/vnd.pagerduty+json;version=2.0",
}


def get_data(endpoint, key, headers, params=None):
    data = []
    offset = 0
    while True:
        page_params = {"limit": 100, "offset": offset}
        if params:
            page_params.update(params)
        resp = requests.get(
            f"{BASE_URL}/{endpoint}", headers=headers, params=page_params
        )
        resp.raise_for_status()
        result = resp.json()
        chunk = result.get(key, [])
        if not isinstance(chunk, list):
            raise ValueError(f"Expected a list for key '{key}', got: {type(chunk)}")
        data.extend(chunk)
        if not result.get("more"):
            break
        offset += 100
    return data


def write_csv(filename, data, fields):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in fields})


def anonymize_name(entity_type, index):
    return f"{entity_type}{index}"


def extract_summary(api_key, anonymize=False):
    runtime = datetime.now().strftime("%Y%m%d_%H%M")
    headers = dict(API_HEADERS_TEMPLATE)
    headers["Authorization"] = f"Token token={api_key}"
    os.makedirs(f"pagerduty_export_{runtime}", exist_ok=True)

    name_maps = {
        key: {}
        for key in [
            "users",
            "services",
            "escalation_policies",
            "schedules",
            "teams",
            "integrations",
        ]
    }
    id_maps = {
        key: {}
        for key in [
            "users",
            "services",
            "escalation_policies",
            "schedules",
            "teams",
            "integrations",
        ]
    }
    name_counters = {key: 1 for key in name_maps}

    def get_anon_name(entity_type, original):
        if original not in name_maps[entity_type]:
            name_maps[entity_type][original] = anonymize_name(
                entity_type[:-1].capitalize(), name_counters[entity_type]
            )
            name_counters[entity_type] += 1
        return name_maps[entity_type][original]

    print("🔍 Fetching teams...")
    teams = get_data("teams", "teams", headers)
    team_data = []
    for t in teams:
        tid = t.get("id")
        name = t.get("name", "")
        id_maps["teams"][tid] = name
        team_data.append(
            {
                "id": tid,
                "name": get_anon_name("teams", name) if anonymize else name,
                "description": "" if anonymize else t.get("description", ""),
            }
        )
    write_csv(
        f"pagerduty_export_{runtime}/teams.csv",
        team_data,
        ["id", "name", "description"],
    )

    print("🔍 Fetching users...")
    users = get_data("users", "users", headers)
    user_data = []
    for u in users:
        uid = u.get("id")
        name = u.get("name", "")
        id_maps["users"][uid] = name
        team_id = u.get("teams", [{}])[0].get("id", "") if u.get("teams") else ""
        user_data.append(
            {
                "id": uid,
                "name": get_anon_name("users", name),  # Always anonymize users
                "email": "hidden@example.com",  # Always redact email
                "role": u.get("role", ""),
                "team_id": team_id,
            }
        )
    write_csv(
        f"pagerduty_export_{runtime}/users.csv",
        user_data,
        ["id", "name", "email", "role", "team_id"],
    )

    print("🔍 Fetching schedules...")
    schedules = get_data("schedules", "schedules", headers)
    schedule_data = []
    for s in schedules:
        sid = s.get("id")
        name = s.get("name", "")
        id_maps["schedules"][sid] = name
        layers = s.get("schedule_layers", [])
        total_users = sum(len(layer.get("users", [])) for layer in layers)
        team_id = s.get("teams", [{}])[0].get("id", "") if s.get("teams") else ""
        schedule_data.append(
            {
                "id": sid,
                "name": get_anon_name("schedules", name) if anonymize else name,
                "time_zone": s.get("time_zone", ""),
                "num_layers": len(layers),
                "total_users": total_users,
                "team_id": team_id,
            }
        )
    write_csv(
        f"pagerduty_export_{runtime}/schedules.csv",
        schedule_data,
        ["id", "name", "time_zone", "num_layers", "total_users", "team_id"],
    )

    print("🔍 Fetching escalation policies...")
    policies = get_data("escalation_policies", "escalation_policies", headers)
    esc_data = []
    for p in policies:
        pid = p.get("id")
        name = p.get("name", "")
        id_maps["escalation_policies"][pid] = name
        user_ids = []
        schedule_ids = []
        for rule in p.get("escalation_rules", []):
            for target in rule.get("targets", []):
                target_type = target.get("type", "")
                target_id = target.get("id")
                if target_type == "user_reference" and target_id in id_maps["users"]:
                    user_ids.append(target_id)
                elif (
                    target_type == "schedule_reference"
                    and target_id in id_maps["schedules"]
                ):
                    schedule_ids.append(target_id)
        team_id = p.get("teams", [{}])[0].get("id", "") if p.get("teams") else ""
        esc_data.append(
            {
                "id": pid,
                "name": (
                    get_anon_name("escalation_policies", name) if anonymize else name
                ),
                "user_ids": ", ".join(user_ids),
                "schedule_ids": ", ".join(schedule_ids),
                "team_id": team_id,
            }
        )
    write_csv(
        f"pagerduty_export_{runtime}/escalation_policies.csv",
        esc_data,
        ["id", "name", "user_ids", "schedule_ids", "team_id"],
    )

    print("🔍 Fetching services...")
    services = get_data(
        "services", "services", headers, params={"include[]": "integrations"}
    )
    service_data = []
    integration_details = []
    for svc in services:
        sid = svc.get("id")
        name = svc.get("name", "")
        id_maps["services"][sid] = name
        ep_id = svc.get("escalation_policy", {}).get("id", "")
        team_id = svc.get("teams", [{}])[0].get("id", "") if svc.get("teams") else ""
        integrations = [i.get("summary", "") for i in svc.get("integrations", [])]
        service_data.append(
            {
                "id": sid,
                "name": get_anon_name("services", name) if anonymize else name,
                "escalation_policy_id": ep_id,
                "integrations": ", ".join(integrations),
                "team_id": team_id,
            }
        )
        for intg in svc.get("integrations", []):
            intg_id = intg.get("id")
            intg_name = intg.get("summary", "")
            intg_vendor = intg.get("vendor", None)
            id_maps["integrations"][intg_id] = intg_name
            integration_details.append(
                {
                    "id": intg_id,
                    "summary": (
                        get_anon_name("integrations", intg_name)
                        if anonymize
                        else intg_name
                    ),
                    "integration_type": intg.get("type", ""),
                    "vendor": intg_vendor.get("summary", "") if intg_vendor else "",
                    "service": sid,
                }
            )
    # Write service data to CSV
    write_csv(
        f"pagerduty_export_{runtime}/services.csv",
        service_data,
        ["id", "name", "escalation_policy_id", "integrations", "team_id"],
    )

    # Provide a summary of integration types
    integration_types = [i.get("integration_type", "") for i in integration_details]
    write_csv(
        f"pagerduty_export_{runtime}/integration_types.csv",
        [
            {"integration_type": t, "count": integration_types.count(t)}
            for t in set(integration_types)
        ],
        ["integration_type", "count"],
    )

    # Write integration details to a separate CSV
    write_csv(
        f"pagerduty_export_{runtime}/integration_details.csv",
        integration_details,
        ["id", "summary", "integration_type", "vendor", "service"],
    )

    print(f"\n✅ Export complete! Files saved to ./pagerduty_export_{runtime}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export PagerDuty configuration to CSV"
    )
    # add mutually exclusive arguments for sourcing the token
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--token", help="Your PagerDuty API token (read-only)")
    group.add_argument(
        "-e",
        "--env",
        help="Name of environment variable containing your PagerDuty API token (read-only). Default is PAGERDUTY_TOKEN",
        default="PAGERDUTY_TOKEN",
    )
    parser.add_argument(
        "-a",
        "--anonymise",
        action="store_true",
        help="Replace names with generic labels for services, schedules, policies, and teams",
    )
    args = parser.parse_args()

    if args.env:
        args.token = os.environ.get(args.env)
        if not args.token:
            raise ValueError(f"Environment variable '{args.env}' not set or empty.")
    extract_summary(api_key=args.token, anonymize=args.anonymise)
