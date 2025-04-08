#!/bin/bash
set -o pipefail

#
# The purpose of this script is to take all of the commits from the "default"
# branch and merge them onto the "master" branch. When we are doing this, we
# will skip any commit that modifies anything in the `./circleci` directory.
#

# Tell git to never use a pager
git config --global core.pager cat

branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" != "default" ] ; then
  echo "The automerge script is only intended for use on the 'default' branch." >&2
  exit 1
fi

# Look up the remote origin, and alter it to use https with oauth.
origin=$(git config --get remote.origin.url) 

# We need to do a little dance to get git to recognize the top commit of the master branch
git fetch "$origin" master 
git checkout master 
git checkout - 

# Commits on the 'default' branch not yet on master in reverse order (oldest first),
# ignoring any commit that modifies only files in .circleci or in .github
# TODO: This should ignore if _any_ change is in one of these directories, not all changes.
commits=$(git log master..HEAD --pretty=format:"%h" -- . ':!.circleci' ':!.github' | sed '1!G;h;$!d')

# If nothing has changed, bail without doing anything.
if [ -z "$commits" ] ; then
  echo "Nothing to merge"
  echo "https://i.kym-cdn.com/photos/images/newsfeed/001/240/075/90f.png"
  exit 0
fi

# Check to see who the top author is
author="$(git log --pretty=format:"%an %ae" -1)"

# Let commits by any user other than Pantheon Automation sit in the
# default branch until we get a commit from Pantheon Automation.
if [ "$author" != "Pantheon Automation bot@getpantheon.com" ] ; then
  echo "Top commit is not by Pantheon Automation bot. Leaving the following commits on default branch:"
  git log master..HEAD --pretty=format:"%Cred%h %Cblue%cd %Cgreen%an%Creset %s"
  exit 0
fi

echo ":::::::::: Auto-merging to master ::::::::::"
set -ex

# Log our actions (e.g. cherry-picks) as Pantheon Automation
git config --global user.email "<bot@getpantheon.com>"
git config --global user.name "Pantheon Automation"

git checkout master
for commit in $commits ; do
  git cherry-pick "$commit"
done

# If the top commit looks like an upstream update, make sure that it is
# authored by Pantheon Automation.
current_comment=$(git log --pretty=format:"%s" -1)
if [[ "$current_comment" == *"see https://"* ]] ; then
  git commit --amend --author="Pantheon Automation <bot@getpantheon.com>" -m "$current_comment" 
fi

git checkout -
git rebase master

# Push updated master and default branches back up
git push -u "$origin" master
git push -u "$origin" default --force
