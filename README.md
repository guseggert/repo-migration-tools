This contains tools for migrating files and issues from one GitHub repo to another, while preserving the commit history.

## Prerequisites

- Install the GitHub CLI and login using `gh auth login`
- Install Python 3.11
- Install pipenv: `pip install --user pipenv`
- Clone this repo, `cd` to it, and activate the virtualenv: `pipenv shell`

## Migrating code

See also the help using `python migrate.py repo --help`.

This will move files match by the globs from the source repo into a subdirectory in the destination repo. This happens locally, and the command will print the local directory of the destination repo so that the change can be inspected, pushed to a branch, and then a PR opened.

This also adds a note to the bottom of each git commit message indicating that the commit was moved, and from where. For merge commits, the message is also updated so that it points to the original repo, so that the GitHub link continues to work.

```
python migrate.py repo \
  --source-repo ipfs/tar-utils \
  --glob '*.go' --glob 'README.md' \
  --dest-repo ipfs/libkubo \
  --dest-subdir target \
  --dest-branch migrate-tar-utils
```

## Migrating issues

There's a command for migrating open issues between repos. A prefix will be added to the issue title showing the repo that it came from.

```
python migrate.py issues \
  --source-repo ipfs/tar-utils \
  --dest-repo ipfs/libkubo
```

## Closing PRs
There is no easy way to "transfer" PRs. This command will close all open PRs in the source repo and leave a comment asking the requester to re-open in the destination repo.

```
python migrate.py clean-pull-requests \
  --source-repo ipfs/tar-utils \
  --dest-repo ipfs/libkubo
```

## Example Workflow
1. Run the command in [Migrating code](#migrating-code)
1. `cd` to the temp dir where the destination repo was left
1. Perform any cleanup actions like running `go mod tidy`, and run any builds/tests
1. Push the branch to remote and open a PR
1. Wire up the change into upstream dependencies
    - e.g. in Go, navigate to its local Git repo and run `go get github.com/<owner>/<name>@<branch>` using the `--dest-branch` that you used in step 1.
    - Open a draft PR for the upstream dependency, so that CI runs, and mention it in the migration PR so the reviewer can see that the code works upstream
	- If there are many consumers of the old repo, consider a graceful migration:
	    - Stub out types by making type aliases that point to types in the new repo
		- Add deprecation notices to the types in the old repo
		- Treat the same as other upstream dependencies (open a PR, run CI, mention in the migration PR, etc.)
1. Once the PR is merged
    - Tag a new version
    - Update the upstream PRs to consume the versioned release, mark the PRs as ready, and then merge once approved
    - Run the `issues` command to migrate open issues to the new repo
    - Run the `clean-pull-requests` command to close open PRs
	- Archive the old repo
	    - If doing a "graceful migration" then tag & release a final version before archiving

