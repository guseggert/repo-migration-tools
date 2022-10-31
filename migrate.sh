#!/bin/bash

set -ex

# set the FORCE env var when testing locally on repos that haven't been cloned
# generally you don't want to do this, since it is dangerous

cmd="$1"

pushd -n "$PWD"

case "$cmd" in
    move-repo)
	src_repo_path=$(readlink -f "$2")
	src_branch="$3"
	tgt_repo_path=$(readlink -f "$4")
	tgt_branch="$5"

	cd "$tgt_repo_path"
	git remote add src-repo "$src_repo_path"
	git checkout -b "$tgt_branch"
	git pull src-repo "$src_branch" --allow-unrelated-histories --rebase
	git remote remove src-repo
	;;
    move-glob-to-subdir)
	src_repo_path=$(readlink -f "$2")
	src_branch="$3"
	src_glob="$4"
	tgt_repo_path=$(readlink -f "$5")
	tgt_branch="$6"
	tgt_subdir_path="$7"

	cd "$src_repo_path"
	src_orig_branch="$(git branch --show-current)"
	git checkout "$src_branch"
	git checkout -b tmp-migrate-branch
	git filter-repo ${FORCE:+--force} --path-glob "$src_glob" --to-subdirectory-filter "$tgt_subdir_path" --refs tmp-migrate-branch
	cd "$tgt_repo_path"
	git remote add src-repo "$src_repo_path"
	git checkout -b "$tgt_branch"
	git pull --allow-unrelated-histories --rebase src-repo tmp-migrate-branch
	git remote remove src-repo
	cd "$src_repo_path"
	git checkout "$src_orig_branch"
	git branch -D tmp-migrate-branch
	;;
    *)
	echo "unknown command"; exit 1
esac

popd
