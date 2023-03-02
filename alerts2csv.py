#!/usr/bin/env python3
import argparse
import sys
from pdpyras import APISession
import csv


def was_acknowledged(incident, pd_api_session):
    """
    Return true if the incident's event log contains an acknowledgement
    """
    log_entries = pd_api_session.iter_all(
        "incidents/{}/log_entries".format(incident["id"])
    )
    log_types = (entry["type"] for entry in log_entries)
    return "acknowledge_log_entry" in log_types


def chain(iterables):
    """
    Helper function: concatenates a list of iterators
    """
    for iterable in iterables:
        yield from iterable


# Process cmdline arguments
parser = argparse.ArgumentParser(
    prog="alerts2csv",
    description="Generates a CSV of human-acknowledged alerts associated with a given PagerDuty service name (e.g., mycluster.abcd.p1.openshiftapps.com)",
)
parser.add_argument(
    "service_name",
    nargs="+",
    help="(partial) PagerDuty service name(s). Specify '-' here to read newline-separated entries from stdin",
)
parser.add_argument(
    "-s",
    "--since",
    help="start of the time window in ISO-8601 format (e.g., 2023-01-01) (default: 1 month ago)",
    metavar="DATETIME",
)
parser.add_argument(
    "-u",
    "--until",
    help="end of the time window in ISO-8601 format (e.g., 2023-01-01) (default: now)",
    metavar="DATETIME",
)
parser.add_argument(
    "-k",
    "--pd-api-keyfile",
    help="path of the text file containing your PagerDuty API key (default: %(default)s)",
    default=".pdapikey",
    metavar="PATH",
)
parser.add_argument(
    "-o",
    "--output-path",
    help="path where the output CSV should be written (default: %(default)s)",
    default="alerts.csv",
    metavar="PATH",
)
args = parser.parse_args()

# Load PD API key
with open(args.pd_api_keyfile, "r") as f:
    pd_api_key = f.readline().strip()

if len(pd_api_key) < 20:
    sys.exit("FATAL: bad PagerDuty API key")

# Log into PD
pd = APISession(pd_api_key)

# Process provided service names
service_names = args.service_name
if len(args.service_name) == 1 and args.service_name[0] == "-":
    service_names = []
    # Read from stdin
    for line in sys.stdin:
        if line.strip() == "":
            break
        service_names.append(line.strip())


# Find the service
selected_incident_iters = []
for service_name in service_names:
    try:
        services = pd.list_all("services", params={"query": service_name})
        if len(services) < 1:
            print(
                "ERROR: Unable to find any PagerDuty services with '{}' in the name".format(
                    service_name
                )
            )
            continue
        if len(services) > 1:
            print(
                "WARNING: found more than one PagerDuty service with '{}' in its name. Defaulting to the first one"
            )
        service = services[0]
        print("Downloading incidents for {}...".format(service["name"]))

        # Dowload incidents within the time bounds
        incident_params = {"service_ids": [service["id"]], "timezone": "UTC"}
        if args.since:
            incident_params["since"] = args.since
        if args.until:
            incident_params["until"] = args.until

        incident_iter = pd.iter_all("incidents", params=incident_params)
        acked_incident_iter = (
            inc for inc in incident_iter if was_acknowledged(inc, pd)
        )
        selected_incident_iters.append(acked_incident_iter)
    except Exception as ex:
        print(
            "ERROR: failed to get incidents for {} due to {}. Continuing anyways...",
            service_name,
            ex,
        )


# Write the CSV
with open(args.output_path, "w", newline="") as csvfile:
    fieldnames = [
        "IncidentNum",
        "Timestamp",
        "ClusterName",
        "AlertName",
        "Urgency",
        "URL",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    incident_count = 0
    for incident in chain(selected_incident_iters):
        try:
            writer.writerow(
                {
                    "IncidentNum": incident["incident_number"],
                    "Timestamp": incident["created_at"],
                    "ClusterName": incident["service"]["summary"]
                    .removeprefix("osd-")
                    .split(".")[0],
                    "AlertName": incident["title"].split("(")[0].strip(),
                    "Urgency": incident["urgency"],
                    "URL": incident["html_url"],
                }
            )
            incident_count += 1
        except Exception as ex:
            print(
                "ERROR: failed to write a row due to {}. Continuing anyways...".format(
                    ex
                )
            )

print("Saved {} incidents to {}".format(incident_count, args.output_path))
