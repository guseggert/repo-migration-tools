#!/bin/bash

set -e

[ $# != 1 ] && echo "usage: $0 <dest_repo>" && exit 1

dest_repo=$1

echo "Collecting issues..."
ids=$(gh issue list -s all -L 10000 --json number | jq -r '.[] | .number')

for id in $ids; do
    title=$(gh issue view "$id" --json title | jq -r .title)
    repo=$(gh repo view --json nameWithOwner | jq -r .nameWithOwner)
    new_title="$repo: $title"
    echo "Transferring issue $id ($title) to $dest_repo as \"$new_title\""
    [ -n "$DRYRUN" ] && continue
    new_url=$(gh issue transfer "$id" "$dest_repo")
    gh issue edit "$new_url" --title "$new_title" >/dev/null
done	  
