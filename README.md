# alerts2csv
A quick-and-dirty CLI tool for downloading PagerDuty alerts to CSV

## Installation
Before you begin, you'll need:
* Python 3.8+ and `pip`
  * RHEL users: run `sudo dnf install python39 python39-pip` 
  * Fedora users: run `sudo dnf install python3 python3-pip` (although they're probably already installed) 
* a PagerDuty User/API token/key ([instructions](https://support.pagerduty.com/docs/api-access-keys#section-generate-a-user-token-rest-api-key))
* the (PDPYRAS)[https://github.com/PagerDuty/pdpyras] pip package
  * run `pip3 install pdpyras` or `pip3.9 install pdpyras`

Then just clone this repo, `cd` into it, drop your PagerDuty API key into a text file called `.pdapikey`, and run `chmod +x ./alerts2csv.py`.

## Usage
General usage is explained by running `./alerts2csv.py --help`
```
usage: ./alerts2csv.py [-h] [-s DATETIME] [-u DATETIME] [-k PATH] [-o PATH] service_name [service_name ...]

Generates a CSV of human-acknowledged alerts associated with a given PagerDuty service name (e.g., mycluster.abcd.p1.openshiftapps.com)

positional arguments:
  service_name          (partial) PagerDuty service name(s). Specify '-' here to read newline-separated entries from stdin

options:
  -h, --help            show this help message and exit
  -s DATETIME, --since DATETIME
                        start of the time window in ISO-8601 format (e.g., 2023-01-01) (default: 1 month ago)
  -u DATETIME, --until DATETIME
                        end of the time window in ISO-8601 format (e.g., 2023-01-01) (default: now)
  -k PATH, --pd-api-keyfile PATH
                        path of the text file containing your PagerDuty API key (default: .pdapikey)
  -o PATH, --output-path PATH
                        path where the output CSV should be written (default: alerts.csv)
```

### Examples
The following command would download all acknowledged alerts that occurred during January 2023 for the PagerDuty service named "mycluster.abcd" and write them to a CSV file named "mycluster.alerts.csv"
```bash
./alerts2csv.py -o "mycluster.alerts.csv" --since=2023-01-01 --until=2023-01-31 "mycluster.abcd"
```
The following command would download all acknowledged alerts that occurred between 9AM and 5PM UTC on March 1st, 2023 for a service named "test-cluster" to the default "alerts.csv"
```bash
./alerts2csv.py -s "2023-03-01T09:00:00Z" -u "2023-03-01T17:00:00Z" "test-cluster"
```
Finally, the following command would download all ack'd alerts from the past month for any PagerDuty service connected to clusters under the OCM org. ID "ABCD12345wxyz" to "wxyz.csv"
```bash
ocm get /api/accounts_mgmt/v1/subscriptions -p search="organization_id like 'ABCD12345wxyz'" | jq -r '.items[] | select(.managed==true and .status=="Active") | .console_url' | cut -d. -f3- | ./alerts2csv.py --output-path=wxyz.csv -
# Note: the hypen at the end is important!
```
