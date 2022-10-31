This is a script for migrating files from one repo to other repo, while preserving the commit history.

There is also a script for moving GitHub issues from one repo to another.

## Migrating code
### Prerequisites

- Install filter-repo https://github.com/newren/git-filter-repo

### Usage

First, clone both repos locally. Do not reuse existing clones--they should be new, clean clones.

The result of these commands will be a new branch on the target repo containing the changes. You should then open a PR to merge the branch into main/master. 

Note that this does not migrate tags.

#### Copy a repo to a subdir of another repo
`./migrate.sh move-repo <src_repo_path> <src_repo_branch> <dest_repo_path> <dest_repo_branch>`

Example: suppose I want to move all files from the master branch of repo `test/a` into the root of repo `test/b`, on a new branch called `consolidate-things`:

```
$ tree test
test
├── a
│   └── file-a
└── b
    └── file-b

$ ./migrate.sh move-repo test/a master test/b consolidate-things

$ tree test
test
├── a
│   └── file-a
└── b
    ├── file-a
    └── file-b

```

#### Copy a glob of files from a repo to a subdir of another repo
`./migrate.sh move-glob-to-subdir <src_repo_path> <src_repo_branch> <src_glob> <dest_repo_path> <dest_repo_branch> <dest_subdir>`

Suppose I want to move all files matching a pattern `dir-a/*.go` from the master branch of repo `test/a` into a subdirectory `from-a` of repo `test/b`, on a new branch called `consolidate-things`:

```
$ tree test
test
├── a
│   ├── dir-a
│   │   └── a.go
│   └── file-a
└── b
    └── file-b

$ ./migrate.sh move-glob-to-subdir test/a master 'dir-a/*.go' test/b consolidate-things from-a

$ tree test
test
├── a
│   ├── dir-a
│   │   └── a.go
│   └── file-a
└── b
    ├── file-b
    └── from-a
        └── dir-a
            └── a.go
```

## Migrating Issues
### Prerequisites
- `jq`
- GitHub CLI (`gh` command), with auth configured as necessary

### Usage
Repos are slways of the form `owner/name`, e.g. if the URL is `github.com/foo/bar` then the repo you pass should be `foo/bar`.

To migrate issues:
```
cd src_repo
migrate-issues.sh <dest_repo>
```

This will move all issues from `src_repo` into `dest_repo` and rename them to begin with `src_repo`, like `owner/name: Some Issue`.

You can dryrun a transfer to see what the result will be, without actually executing it, by setting the `DRYRUN` environment variable.
