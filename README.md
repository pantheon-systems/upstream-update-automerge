# Upstream Update "Automerge"

This action runs the "automerge" script used to deploy changes from the `default` branch to the `master` branch on Pantheon's upstream repositories (`wordpress`, `drops-7`). Automerge copies commits to the `master` branch if the latest commit on `default` is authored by `"Pantheon Automation <bot@getpantheon.com>"`. It then rebases the `default` branch onto `master` and updates `default` with a force push. Commits that edit `.circleci/` or `.github/` directories are not copied to `master`.

## Usage 
```
name: Automerge
on:
  push:
    branches:
      - default

permissions:
  contents: write

jobs:
  automerge:
    runs-on: ubuntu-latest
    steps:
        - uses: actions/checkout@v4
          with:
            fetch-depth: 0
        - uses: pantheon-systems/upstream-update-build@v1
          env:
            PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
```

### PAT_TOKEN
`PAT_TOKEN` must be a personal access token with permission to force-push to branches of the project this action is run on.

## Test

python3 test.py


## Previous Iterations
This action is implemented from a version of the script that was previously deployed as a docker image at `quay.io/getpantheon/upstream-update-build:1.x` and used in the CI scripts for `pantheon-systems/WordPress` and `pantheon-systems/drops-7`. The source for that docker image can still be found on the [1.x branch](https://github.com/pantheon-systems/upstream-update-build/tree/1.x).