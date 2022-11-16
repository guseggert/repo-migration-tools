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

