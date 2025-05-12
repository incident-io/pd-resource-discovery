# PD Resource Discovery

Whether you’re trialling or migrating to [incident.io](http://incident.io/) On-call, we want to make your switch from PagerDuty as seamless as possible.

To do that, we’ve put together a simple resource discovery script. It creates a high-level export of your PagerDuty account which we can review together.

With the export, we can:

- Understand the size and complexity of your current setup
- Plan a migration that fits your needs
- Spot potential blockers early
- Give you a clear, surprise-free path to going live with incident.io

---

## What this script does

This script connects to your PagerDuty account using a read-only API token and exports a complete picture of your current configuration.

After running, the script creates a `pagerduty_export/` folder containing:

| File | Contents |
| --- | --- |
| `users.csv` | List of anonymised PagerDuty users and their roles. *These entries are **always anonymised** so we don’t collect names, email addresses or any other personally identifiable information (PII).* |
| `teams.csv` | Defined teams and their descriptions. |
| `schedules.csv` | On-call schedules with layers and user counts. |
| `escalation_policies.csv` | Escalation Policies with their linked users and schedules. |
| `services.csv` | Services with their alert integrations and linked Escalation Policies. |

The resulting set of `.csv` files can be reviewed by you, before sharing with us directly.


## Security and anonymisation

Whilst it’s helpful for us to understand the context used within your PagerDuty account (i.e. team names, service names, etc.), and allows us to talk you you about specifics during the migration, we know this information can be sensitive, especially in regulated or security-conscious environments.

Regardless of configuration, we don’t collect any personally identifiable information (PII). The users table is only necessary for us to understand which users exist and where they feature in the rest of the PagerDuty configuration. We don’t need, and therefore don’t collect, names, email addresses or any contact information. 

If you do have concerns around sharing the other information, we’ve built in an **anonymisation mode** that replaces all team, service, schedule, and policy names with generic labels (e.g. `Service1`, `Schedule4`, etc.)

Anonymous mode **keeps integration names intact** so we can still understand what tools are in use. This is integral to us understanding your configuration, but we only collect the integration name, and not any configuration.

## How to run it

### Requirements:

- Python 3
- A PagerDuty **read-only API token**

### Step 1: Create a read-only API token in PagerDuty

1. In the PagerDuty dashboard, navigate to **Integrations** → **API Access Keys** under **Developer Tools**.
2. Click **Create New API Key**.
3. Enter a **Description** to help you identify the key later
4. Check **Read-only API Key** – we only need access to read data, not make changes.
5. Click **Create Key**. 

### Step 2: Run the script

```bash
python3 resource-discovery.py --token YOUR_PD_API_TOKEN
```

To anonymise your export:

```bash
python3 resource-discovery.py --token YOUR_PD_API_TOKEN --anonymise
```

## Sharing with us

Once you’ve run the script:

1. Review the contents of the `.csv` files to ensure you’re happy with the data we’ve pulled.
2. Send the contents of the `pagerduty_export/` folder back to us. 
3. We’ll review the data and share back a detailed migration plan tailored to your setup

This process helps us get ahead of any custom configurations or edge cases, and ensures your switch to incident.io is smooth, fast, and well supported.# pd-resource-discovery
