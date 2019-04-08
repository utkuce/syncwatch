#!/bin/bash
i=0
for filename in *.svg; do
    mv "$filename" "avatar$i.svg"
	i=$((i+1))
done