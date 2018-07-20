#!/bin/bash

#
# The purpose of this script is to take all of the commits from the "default"
# branch and merge them onto the "master" branch. When we are doing this, we
# will skip any commit that modifies anything in the `./circleci` directory.
#
# We expect that the environment variable GITHUB_TOKEN is already defined.
#
branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" != "default" ] ; then
  echo "The automerge script is only intended for use on the 'default' branch." >&2
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ] ; then
  echo "The automerge script requires that the GITHUB_TOKEN environment variable be defined." >&2
fi

# Look up the remote origin, and alter it to use https with oauth.
origin=$(git config --get remote.origin.url | sed -e 's#git@github.com:#https://github.com/#')
origin=$(echo $origin | sed -e "s#https://github.com#https://$GITHUB_TOKEN:x-oauth-basic@github.com#")

# We need to do a little dance to get git to recognize the top commit of the master branch
git fetch $origin master | sed -e "s#$GITHUB_TOKEN#[REDACTED]#g"
git checkout master
git checkout -

# Commits on the 'default' branch not yet on master in reverse order (oldest first),
# ignoring any commit that modifies only files in .circleci
commits=$(git log master..HEAD --pretty=format:"%h" -- . ':!.circleci' | sed '1!G;h;$!d')

# If nothing has changed, bail without doing anything.
if [ -z "$commits" ] ; then
  echo "Nothing to merge"
  echo "https://i.kym-cdn.com/photos/images/newsfeed/001/240/075/90f.png"
  exit 0
fi

echo ":::::::::: Auto-merging to master ::::::::::"

set -ex

# Log our actions (e.g. cherry-picks) as Pantheon Automation
git config --global user.email "<bot@getpantheon.com>"
git config --global user.name "Pantheon Automation"

git checkout master
for commit in $commits ; do
  git cherry-pick $commit
done

# If the top commit looks like an upstream update, make sure that it is
# authored by Pantheon Automation.
current_comment=$(git log --pretty=format:"%s" -1)
if [[ "$current_comment" == *"see https://"* ]] ; then
  git commit --amend --author="Pantheon Automation <bot@getpantheon.com>" -m "$current_comment"
fi

git checkout -
git rebase master

set +ex

# Push updated master and default branches back up
git push -u $origin master | sed -e "s#$GITHUB_TOKEN#[REDACTED]#g"
git push -u $origin default --force | sed -e "s#$GITHUB_TOKEN#[REDACTED]#g"
