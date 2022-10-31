#!/bin/bash

set -e

# set the FORCE env var when testing locally on repos that haven't been cloned
# generally you don't want to do this, since it is dangerous

[ $# == 0 ] && echo "must specify a command, one of: move-repo, move-glob-to-subdir" && exit 1

cmd="$1"

pushd -n "$PWD" >/dev/null

case "$cmd" in
    move-repo)
	[ $# != 5 ] && echo "usage: $0 move-repo <src_repo_path> <src_branch> <tgt_repo_path> <tgt_branch>" && exit 1
	src_repo_path=$(readlink -f "$2")
	src_branch="$3"
	tgt_repo_path=$(readlink -f "$4")
	tgt_branch="$5"

	cd "$tgt_repo_path"
	git remote remove src-repo 2>/dev/null || true
	git remote add src-repo "$src_repo_path"
	git checkout -B "$tgt_branch"
	git pull --allow-unrelated-histories --no-rebase src-repo "$src_branch"
	git remote remove src-repo
	;;
    move-glob-to-subdir)
	[ $# != 7 ] && echo "usage: $0 move-glob-to-subdir <src_repo_path> <src_branch> <src_glob> <tgt_repo_path> <tgt_branch> <tgt_subdir_path>" && exit 1
	src_repo_path=$(readlink -f "$2")
	src_branch="$3"
	src_glob="$4"
	tgt_repo_path=$(readlink -f "$5")
	tgt_branch="$6"
	tgt_subdir_path="$7"

	cd "$src_repo_path"
	src_orig_branch=$(git branch --show-current)
	git checkout "$src_branch"
	git checkout -B tmp-migrate-branch
	git filter-repo ${FORCE:+--force} --path-glob "$src_glob" --to-subdirectory-filter "$tgt_subdir_path" --refs tmp-migrate-branch
	cd "$tgt_repo_path"
	git remote remove src-repo 2>/dev/null || true
	git remote add src-repo "$src_repo_path"
	git checkout -B tmp-migrate-branch
	git pull --allow-unrelated-histories --no-rebase src-repo tmp-migrate-branch
	git remote remove src-repo
	git checkout -B "$tgt_branch"
	git merge tmp-migrate-branch
	git branch -D tmp-migrate-branch
	cd "$src_repo_path"
	git checkout "$src_orig_branch"
	git branch -D tmp-migrate-branch
	;;
    *)
	echo "unknown command"; exit 1
esac

popd
