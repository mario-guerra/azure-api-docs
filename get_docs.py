#!/usr/bin/env python3

# Create a csv file containing all the Azure REST API docs files in the form:
# tup0, tup1, latest_stable, latest_preview

import glob
import os
import subprocess
import sys

# Create a mapping of a "two-tuple" to all JSON files matching the tuple
# The components of the tuple are:
# - the file name up to the "stable" or "preview" segment
# - the remainder of the filename after the "version" segment
docs = {}

# return the date of the last commit as a UNIX Timestamp (seconds since epoch)
def last_commit_date(file):
    p = subprocess.run(f'git log -1 --format=%ct {file}', shell=True, capture_output=True)
    return p.stdout.decode().strip()


# There are cases (e.g. apimangement) where multiple versions are updated in the same commit.
# For these cases we fall back to using lexicographic order.
def latest(tup, str):
    files = [x for x in docs[tup] if str in x]
    # If no matching files return None
    if not files:
        return None
    dates = [last_commit_date(x) for x in files]
    latest = max(dates, default=None)
    # If latest is unique, we are done
    if dates.count(latest) == 1:
        return files[dates.index(latest)]
    print(f'Warning! multiple latest files for {tup[0]} / {tup[1]}', file=sys.stderr)
    return max([files[i] for i in range(len(files)) if dates[i] == latest])


# Pull in the latest version of the Azure API docs (NO shallow clone)
os.system('rm -rf azure-rest-api-specs')
os.system('git clone https://github.com/Azure/azure-rest-api-specs.git')
os.chdir('azure-rest-api-specs')

for v1 in ["data-plane", "resource-manager"]:
    for v2 in ["stable", "preview"]:
        files = glob.glob(f'specification/*/{v1}/**/{v2}/**/*.json', recursive=True)
        for file in files:
            if '/examples/' not in file:
                parts = file.split('/')
                indx = parts.index(v2)
                tup = ( '/'.join(parts[0:indx]), '/'.join(parts[indx+2:]) )
                docs[tup] = [*docs.get(tup, []), file]

# For each entry in docs, find the latest (by git commit date) "stable" and "preview" file
for tup in docs.keys():
    latest_stable = latest(tup, '/stable/')
    latest_preview = latest(tup, '/preview/')
    # Only keep latest_preview if it is more recent than latest_stable
    if latest_preview is not None and latest_stable is not None:
        if last_commit_date(latest_preview) < last_commit_date(latest_stable):
            latest_preview = None
    print(f'{tup[0]},{tup[1]},{latest_stable},{latest_preview}')
