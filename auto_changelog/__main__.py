"""
Generage a changelog straight from your git commits.

Usage: auto-changelog [options]

Options:
    -r=REPO --repo=REPO     Path to the repository's root directory [Default: .]
    -t=TITLE --title=TITLE  The changelog's title [Default: Changelog]
    -r=REV --rev=REV        REV (see git-rev-parse) for commit listing [Default: master]
    --include-branches=BRA  comma separated fnmatch pattern for including branches [Default: *]
    --exclude-branches=BRA  comma separated fnmatch pattern for excluding branches [Default:]
    -T=REV --tag-filter=PAT tag filter pattern (see fnmatch) [Default: *]
    --dont-keep-unreleased  Don't keep unreleases commits
    -d=DESC --description=DESC
                            Your project's description
    -o=OUTFILE --output=OUTFILE
                            The place to save the generated changelog
                            [Default: CHANGELOG.md]
    -t=TEMPLATEDIR --template-dir=TEMPLATEDIR
                            The directory containing the templates used for
                            rendering the changelog
    -h --help               Print this help text
    -V --version            Print the version number
"""

import os
import sys

import docopt
import fnmatch

from .parser import traverse
from .generator import generate_changelog
from . import __version__


def main():
    args = docopt.docopt(__doc__, version=__version__)

    if args.get('--template-dir'):
        template_dir = args['--template-dir']
    else:
        # The templates are sitting at ./templates/*.jinja2
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(BASE_DIR, 'templates')

    keep_unreleased = True
    if args.get('--dont-keep-unreleased'):
        keep_unreleased = False

    tfp = args['--tag-filter']
    if tfp is None:
        tfp = '*'

    ib = args['--include-branches']
    if ib is None:
        ib = ['*']
    else:
        ib = ib.split(',')
    eb = args['--exclude-branches']
    if eb is None:
        eb = []
    else:
        eb = eb.split(',')

    try:
        # Traverse the repository and group all commits to master by release
        tags, unreleased = traverse(args['--repo'], rev=args['--rev'],
                                    keep_unreleased=keep_unreleased,
                                    tag_filter=tfp, include_branches=ib,
                                    exclude_branches=eb)
    except ValueError as e:
        print('ERROR:', e)
        sys.exit(1)

    changelog = generate_changelog(
        template_dir=template_dir,
        title=args['--title'],
        description=args.get('--description'),
        unreleased=unreleased,
        tags=tags)

    # Get rid of some of those unnecessary newlines
    # changelog = changelog.replace('\n\n\n', '\n')

    with open(args['--output'], 'w') as f:
        f.write(changelog)


if __name__ == "__main__":
    main()
