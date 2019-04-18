"""
The parser module will traverse a git repository, gathering all the commits
that follow the AngularJS commit message convention, and linking them with
the releases they correspond to.
"""

import git
import fnmatch

from .models import Commit, Tag, Unreleased


def group_commits(tags, commits):
    tags = sorted(tags, key=lambda t: t.date)

    # Adding the tag's commit manually because those seem to be skipped
    commits.extend([Commit(t._commit) for t in tags])

    # Sort the commits and filter out those not formatted correctly
    commits = sorted(commits, key=lambda c: c.date)
    commits = list(filter(lambda c: c.category, commits))

    for index, tag in enumerate(tags):
        # Everything is sorted in ascending order (earliest to most recent),
        # So everything before the first tag belongs to that one
        if index == 0:
            for c in commits:
                if c.date <= tag.date:
                    tag.add_commit(c)
        else:
            prev_tag = tags[index - 1]
            for c in commits:
                if prev_tag.date < c.date <= tag.date:
                    tag.add_commit(c)

    left_overs = list(filter(lambda c: c.date > tags[-1].date, commits))
    return left_overs


def traverse(base_dir, rev='master', keep_unreleased=True,
        include_branches=['*'], exclude_branches=[], tag_filter='*'):
    repo = git.Repo(base_dir)
    tags = [x for x in repo.tags if fnmatch.fnmatch(x.name, tag_filter)]

    if len(tags) < 1:
        raise ValueError('Not enough tags to generate changelog')

    wrapped_tags = []
    for tagref in tags:
        t = Tag(
            name=tagref.name,
            date=tagref.commit.committed_date,
            commit=tagref.commit)
        wrapped_tags.append(t)

    commits = list(repo.iter_commits(rev))
    commits = list(map(Commit, commits))  # Convert to Commit objects

    new_commits = []
    for c in commits:
        branches_tmp = repo.git.branch('-a', '--contains', c.commit_hash)
        add = False
        branches = [x[2:].split()[0].replace('remotes/', '') for x in branches_tmp.splitlines()]
        for b in branches:
            for i in include_branches:
                if fnmatch.fnmatch(b, i):
                    add = True
                    break
        if add:
            for b in branches:
                for i in exclude_branches:
                    if fnmatch.fnmatch(b, i):
                        add = False
                        break
        if add:
            new_commits.append(c)

    # Iterate through the commits, adding them to a tag's commit list
    # if it belongs to that release
    left_overs = group_commits(wrapped_tags, new_commits)

    # If there are any left over commits (i.e. commits created since
    # the last release
    if left_overs and keep_unreleased:
        unreleased = Unreleased(left_overs)
    else:
        unreleased = None

    return wrapped_tags, unreleased
