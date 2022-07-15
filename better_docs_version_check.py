#!/usr/bin/env python3

# Create a "services" file containing all the Azure services (data-plane and mgmt-plane)

from datetime import date
import glob
import json
import re

# Pull in the latest version of the Azure API docs (shallow clone)
# os.system('rm -rf azure-rest-api-specs')
# os.system('git clone --depth 1 https://github.com/Azure/azure-rest-api-specs.git')

# Pull in the latest version of the Azure API docs (shallow clone)
# os.system('rm -rf azure-docs-rest-apis')
# os.system('git clone --depth 1 -b live https://github.com/Azure/azure-docs-rest-apis.git')

# Return true if file is the latest version in azure-rest-api-specs
def is_current(file):
    p = file.split('/')
    is_stable = re.match('.*/stable/.*', file)
    if is_stable:
        latest_stable = sorted(glob.glob('/'.join([*p[:-2], '*', p[-1]])))[-1]
        # if 'Microsoft.Support' in file:
        #     print(f'{file} == {latest_stable}')
        return file == latest_stable
    else:
        # get latest preview
        latest_preview = sorted(glob.glob('/'.join([*p[:-2], '*', p[-1]])))[-1]
        # get latest stable (if it exists)
        stable_versions = glob.glob('/'.join([*p[:-3], 'stable', '*', p[-1]]))
        if len(stable_versions) == 0:
            latest = latest_preview
        else:
            latest_stable = sorted(stable_versions)[-1]
            latest_stable_version = latest_stable.split('/')[-2]
            # if latest version is stable, recommend that (tie goes to stable)
            latest_preview_version = re.sub('-((private)?[Pp]review|beta).*$', '', latest_preview.split('/')[-2])
            latest = latest_stable if latest_preview_version <= latest_stable_version else latest_preview
        # if 'Microsoft.Support' in file:
        #     print(f'{file} == {latest}')
        return file == latest

with open('azure-docs-rest-apis/mapping.json', 'r') as fp:
    mapping = json.load(fp)

# jq -r '.organizations[] | .services[] | .toc_title' mapping.json | sort 
services = [y for x in mapping['organizations'] for y in x['services']]

# We can only document one version of the REST API.
# If what is currently documented is a stable version, make sure it is the most recent stable version.
# If what is currently documented is a preview version, check both preview and stable
#   and recommend the most recent

for service in services:
    docs = {}
    for file in [x['source'] for x in service.get('swagger_files', [])]:
        # print(file)
        parts = file.split('/')
        if parts[0] != 'azure-rest-api-specs':
            continue
        if 'preview' not in parts and 'stable' not in parts:
            continue
        indx = parts.index('preview') if 'preview' in parts else parts.index('stable')
        tup = ( '/'.join(parts[1:indx]), '/'.join(parts[indx+2:]) )
        docs[tup] = [*docs.get(tup, []), file]

    # if len(docs) > 0:
    #     print('Checking {}'.format(service['toc_title']))

    for tup in docs.keys():
        files = docs[tup]
        if not any(is_current(f) for f in files):
            service_name = service['toc_title']
            if len(files) == 1:
                print(f'{service_name} not using current file for {files[0]}')
            else:
                print(f'{service_name} not using current files for {tup[0]}/[version]/{tup[1]}')           
            break
