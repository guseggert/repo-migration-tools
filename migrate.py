import re
import github
import git_filter_repo as fr
import click
from github.Repository import Repository
import tempfile
import os
import subprocess
import pathlib
import urllib3
import datetime
import requests
import fnmatch

def run(args, wd=None):
    if not wd:
        wd = os.getcwd()
    res = subprocess.run(args, cwd=wd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise Exception(f'error running {args[0]}: {res.stdout.decode()} {res.stderr.decode()}')
    return res.stdout.decode().strip()

class RateLimitRetry(urllib3.util.retry.Retry):
    def get_retry_after(self, response):
        reset_time = datetime.datetime.fromtimestamp(int(response.headers["X-RateLimit-Reset"]))
        retry_after = (reset_time - datetime.datetime.now()).seconds + 1
        print(f"Rate limited, retrying after {retry_after} seconds")
        return retry_after


def transfer_issue(auth_token, issue_id, dest_repo_id):
        query = {'query': """
        mutation{
         transferIssue(input:{issueId:"%s",repositoryId:"%s"}) {
          issue {
           number
          }
         }
        }
        """ % (issue_id, dest_repo_id)}
        return requests.post(
            'https://api.github.com/graphql',
            json=query,
            headers={'Authorization': f'Bearer {auth_token}'}
        ).json()['data']['transferIssue']['issue']['number']


def gh_token():
    return run(['gh', 'auth', 'token'])


def new_gh(token):    
    return github.Github(token, retry=RateLimitRetry())


def find_unglobbed_files(repo_dir: str, globs: list[str]):
    files = run(['git', 'ls-files'], wd=repo_dir).split('\n')
    files = [f.strip() for f in files]
    unglobbed_files = []
    for f in files:
        globbed = False
        for glob in globs:
            if fnmatch.fnmatch(f, glob):
                globbed = True
                break
        if not globbed:
            unglobbed_files.append(f)

    return unglobbed_files


class Callbacks(object):
    def __init__(self, source_repo: Repository):
        self._source_repo = source_repo

    def commit_callback(self, commit: fr.Commit, metadata):
        msg = commit.message.decode()
        if 'Merge pull request' in msg:
            msg = re.sub(
                'Merge pull request (.+) from (.*)',
                f'Merge pull request {self._source_repo.full_name}\\1 from \\2',
                msg,
            )
        original_id = commit.original_id
        if original_id:
            msg += f'\n\nThis commit was moved from {self._source_repo.full_name}@{original_id.decode()}'

        commit.message = msg.encode()

       
def clone_repo(tmp_dir: str, repo: Repository) -> str:
    print(f'Cloning {repo.full_name}')
    clone_dir = pathlib.Path(tmp_dir)
    repo_dir = clone_dir / repo.name
    os.mkdir(repo_dir)
    run(['git', 'clone', repo.clone_url, repo_dir])
    return str(repo_dir)

def filter_repo(callbacks: Callbacks, source_repo_path: str, globs, dest_subdir: str):
    glob_args = [arg for glob in globs for arg in ('--path-glob', glob)]
    fr_args = ['--quiet']
    os.chdir(source_repo_path)

    if dest_subdir:
        fr_args += ['--to-subdirectory-filter', dest_subdir]
        
    fr_args += glob_args

    args = fr.FilteringOptions.parse_args(fr_args)
    repo_filter = fr.RepoFilter(args, commit_callback=callbacks.commit_callback)
    repo_filter.run()


def migrate_repo(gh: github.Github, tmp_dir: str, source_repo, source_branch: str, globs: list[str], dest_repo, dest_subdir: str, dest_branch):
        source_gh_repo = gh.get_repo(source_repo)
        dest_gh_repo = gh.get_repo(dest_repo)
        
        if not source_branch:
            source_branch = source_gh_repo.default_branch
            
        source_repo_dir = clone_repo(tmp_dir, source_gh_repo)
        dest_repo_dir = clone_repo(tmp_dir, dest_gh_repo)

        print()
        for unglobbed_file in find_unglobbed_files(source_repo_dir, globs):
            print(f'Skipping unmatched file {unglobbed_file} ')
        print()

        callbacks = Callbacks(source_gh_repo)
        
        filter_repo(callbacks, source_repo_dir, globs, dest_subdir)

        run(['git', 'remote', 'add', 'src-repo', source_repo_dir], wd=dest_repo_dir)
        run(['git', 'checkout', '-B', 'tmp-migrate-branch'], wd=dest_repo_dir)
        run(['git', 'pull', '--allow-unrelated-histories', '--no-rebase', 'src-repo', source_branch], wd=dest_repo_dir)
        run(['git', 'checkout', '-B', dest_branch], wd=dest_repo_dir)
        run(['git', 'merge', 'tmp-migrate-branch'], wd=dest_repo_dir)
        run(['git', 'commit', '--amend', '-m', f'Merge commits from {source_repo}/{source_branch}'], wd=dest_repo_dir)

        return dest_repo_dir


@click.command(name='repo', help='''Move a set of files/dirs from one GitHub repo to another into a subdirectory, preserving the history.

It's recommended to transfer into a new subdirectory to avoid having to deal with conflicts, and then refactoring the directory structure in a separate PR afterwards.

Some commit messages are rewritten so that GitHub links will continue to work correctly, such as links to pull requests in merge commits. Each commit message will also have a note added to the bottom of it explaining that the commit was transferred, and from where. 

This requires an installed and configured GitHub CLI, see https://cli.github.com/.
''')
@click.option('--source-repo', required=True, help='the source repo, in the form <owner>/<name>, such as "ipfs/kubo"')
@click.option('--source-branch', help='the source repo branch to use, defaults to the GitHub master branch (usually "master" or "main")')
@click.option('--glob', required=True, multiple=True, help='glob indicating the set of dirs and files in the source repo to move to the destination repo; can be specified multiple times')
@click.option('--dest-repo', required=True, help='the destination repo, in the form <owner>/<name>, such as "ipfs/kubo"')
@click.option('--dest-subdir', help='the relative subdirectory in the destination repo to place the files from the source repo')
@click.option('--dest-branch', required=True, help='the branch to create in the destination repo to contain the changes')
def migrate_repo_cmd(source_repo, source_branch, glob, dest_repo, dest_subdir, dest_branch):
    globs = list(glob)
    gh = new_gh(gh_token())
    tmp_dir = tempfile.mkdtemp()
    dest_repo_dir = migrate_repo(gh, tmp_dir, source_repo, source_branch, globs, dest_repo, dest_subdir, dest_branch)

    print(f'\n\nWork done in repo: {dest_repo_dir}')
    print('''Switch to that directory and perform any necessary followup actions such as:
    - Finish the merge if there was a conflict
    - Run "go mod tidy" and fix up any dependency issues
    - Wire the change into upstream dependencies, rewrite import paths, and rerun tests
    - Push the branch & open a pull request\n''')


@click.command(name='issues', help='Migrate issues from one repo to another.')
@click.option('--source-repo', required=True)
@click.option('--dest-repo', required=True)
def migrate_issues_cmd(source_repo, dest_repo):
    token = gh_token()
    gh = new_gh(token)
    gh_repo = gh.get_repo(dest_repo)
    repo_id = gh_repo.raw_data['node_id']
    
    issues = gh.search_issues(f'is:issue state:open repo:{source_repo}')
    for issue in issues:
        issue_id = issue.raw_data['node_id']
        new_issue_number = transfer_issue(token, issue_id, repo_id)
        new_issue = gh_repo.get_issue(new_issue_number)
        new_issue.edit(title=f'[{source_repo}] {new_issue.title}')
        print(f'Transferred issue from {issue.html_url} to {new_issue.html_url}')


@click.command(name='clean-pull-requests', help='Clean all open pull requests by leaving a note about the migration and then closing the PR.')
@click.option('--source-repo', required=True)
@click.option('--dest-repo', required=True)
def clean_pull_requests_cmd(source_repo, dest_repo):
    token = gh_token()
    gh = new_gh(token)
    source_gh_repo = gh.get_repo(source_repo)
    dest_gh_repo = gh.get_repo(dest_repo)
    for pr in source_gh_repo.get_pulls(state='open'):
        print(f'Closing PR: {pr.html_url}')
        pr.create_issue_comment(f'This repository has been moved to {dest_gh_repo.html_url}. \
        There is not an easy way to transfer PRs, so if you would like to continue with this PR \
        then please re-open it in the new repository and link to this PR.')
        pr.edit(state='closed')


@click.group()
def migrate():
    pass

migrate.add_command(migrate_repo_cmd)
migrate.add_command(migrate_issues_cmd)
migrate.add_command(clean_pull_requests_cmd)
    
migrate()
