#!/usr/bin/env python3

# Print the path to all previews newer than most recent GA but older than n months.
# We can't just look at the current preview -- we need to go back to the first preview
# that follows the most recent GA.

import glob
import os
import re
import subprocess
import sys
from datetime import datetime

# Create a mapping of a "service" to a set of all "versions" of the service
# - The "service" is the file name up to the "stable" or "preview" segment
# - The "version" is a 3-tuple:
#   - the "stable" or "preview" segment and
#   - the "version" segment immediately following it
#   - the date as "yyyy-mm-dd" string that the version was merged to main
service_versions = {}

# TODO: Return the merge date of the PR that added the file
# For now we just return a date derived from the version or None
def version_date(file, version):
    m = re.match(r'\d{4}-\d{2}-\d{2}', version)
    return m.group(0) if m else None

# Pull in the latest version of the Azure API docs (NO shallow clone)
# os.system('rm -rf azure-rest-api-specs')
# os.system('git clone https://github.com/Azure/azure-rest-api-specs.git')
os.chdir('azure-rest-api-specs')

for v1 in ["data-plane", "resource-manager"]:
    for v2 in ["stable", "preview"]:
        files = glob.glob(f'specification/*/{v1}/**/{v2}/**/*.json', recursive=True)
        for file in files:
            if '/examples/' not in file:
                parts = file.split('/')
                indx = parts.index(v2)
                service = '/'.join(parts[1:indx]) # Skip the "specification" segment
                if service not in service_versions:
                    service_versions[service] = set()
                version = parts[indx+1]
                date = version_date(file, version)
                service_versions[service].add((v2, version, date))

n = 12
print(f'Previews older than {n} months:')

# For each entry in docs, find all previews that are newer than the most recent GA
for service in sorted(service_versions.keys()):
    # For now, because our version_date() function is not very good, we'll ignore
    # any service that has a version without a date.
    if any([x[2] is None for x in service_versions[service]]):
        continue
    # Find the most recent GA
    stable_versions = [x for x in service_versions[service] if x[0] == "stable"]
    latest_stable = max(stable_versions, key=lambda x: x[2]) if stable_versions else None

    # Find all previews newer than the most recent GA
    if latest_stable is None:
        newer_previews = [x for x in service_versions[service] if x[0] == "preview"]
    else:
        newer_previews = [x for x in service_versions[service] if x[0] == "preview" and x[2] > latest_stable[2]]

    if newer_previews:
        # Get the oldest preview that is newer than the most recent GA
        oldest_newer_preview = min(newer_previews, key=lambda x: x[2])

        # If the oldest preview is more than 6 months old, print it
        if (datetime.now() - datetime.strptime(oldest_newer_preview[2], '%Y-%m-%d')).days > n * 30:
            print(f'{service}/{oldest_newer_preview[0]}/{oldest_newer_preview[1]}')
