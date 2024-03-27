#!/bin/bash

rm -rf out; mkdir -p out
awk -F',' '{print $3}' docs.csv | grep -v "None" | while read f; do
  # echo "Linting $f"
  out=$(echo $f | tr "/" "-" | sed 's/^specification-//' | sed 's/.json$/.out/')
  spectral lint -r onerule.yaml azure-rest-api-specs/$f > out/${out} && rm out/${out}
done
