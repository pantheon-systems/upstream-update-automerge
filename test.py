#!/usr/bin/env python
# coding=utf-8

#pylint: disable=broad-except,redefined-outer-name,protected-access,no-name-in-module,not-context-manager

#
# Usage:
#
# Run all tests against PHP 7.3:
#
#   python test-yolo.py 7.3
#
# Run all tests against PHP 7.3, ensuring that the installed patch version
# is PHP 7.3.4:
#
#   python test-yolo.py 7.3.4
#
# Ensure that the installed patch version is PHP 7.3.4:
#
#   python test-yolo.py 7.3.4 ExtensionTestCase.testInstalledPatchVersion
#
#

import os
import subprocess
import shutil
import tempfile
import unittest


class AutomergeTestCase(unittest.TestCase):

    project_under_test = ''
    bindir = ''
    tmpdir = ''
    repo = ''

    def runAutomerge(self):

        # Push our project under test back to our origin
        self.git(["push", "origin", "master"])
        self.git(["push", "origin", "default"])

        # Create another local working copy of our origin for
        # the automerge script to work on
        old_wd = os.getcwd()
        local_working_copy = self.tmpdir + '/working_copy'
        make_local_working_copy = ["git", "clone", "file://" + self.origin, local_working_copy]
        working_copy_output = subprocess.check_output(make_local_working_copy)

        os.chdir(local_working_copy)
        subprocess.check_output(["git", "checkout", "default"])

        cmd = [self.bindir + "/automerge.sh"]
        output = subprocess.check_output(cmd)

        os.chdir(old_wd)

        shutil.rmtree(local_working_copy)

        # Pull from our origin back to our project under test to
        # get the updates made by the automerge script.
        self.switchBranch('master')
        self.git(["pull", "origin", "master"])
        self.switchBranch('default')
        self.git(["reset", "--hard", self.initial])
        self.git(["pull", "origin", "default"])

        return output

    def git(self, args):
        cmd = ["git", "-C", self.repo]
        cmd.extend(args)
        output = subprocess.check_output(cmd)
        return output.strip()

    def commit(self, author, message):
        self.git(["commit", "--author", author, "-m", message])

    def commitAsBot(self, message):
        self.commit('Pantheon Automation <bot@getpantheon.com>', message)

    def commitAsUser(self, message):
        self.commit('J. Doe <doe@example.com>', message)

    def writeFile(self, filename, data, mode = 'w'):
        with open(self.repo + '/' + filename, mode) as f:
            f.write(data)

    def switchBranch(self, branch):
        self.git(["checkout", branch])

    def createBranch(self, branch):
        self.git(["checkout", "-B", branch])

    def addToMaster(self, filename, data, mode = 'w'):
        self.switchBranch('master')
        self.writeFile(filename, data, mode)
        self.git(["add", filename])

    def addToDefault(self, filename, data, mode = 'w'):
        self.switchBranch('default')
        self.writeFile(filename, data, mode)
        self.git(["add", filename])

    def log(self):
        output = self.git(["log", "--pretty=format:%an <%ae> %s"])
        return output
    
    def normalize_string(s):
        return '\n'.join(line.strip() for line in s.strip().splitlines())

    def testAutomerge(self):
        self.project_under_test = os.getcwd()
        self.bindir = self.project_under_test + "/bin"
        self.tmpdir = tempfile.mkdtemp()
        self.repo = self.tmpdir + '/repo'
        self.origin = self.tmpdir + '/origin'

        try:

            # Create a bare repo to serve as our origin

            os.mkdir(self.origin)
            subprocess.check_output(["git", "-C", self.origin, "--bare", "init"])

            # CONTROL:
            #
            # Create a repository with one commit on 'master'.
            # Assert that the single commit exists.

            os.mkdir(self.repo)
            self.git(["init"])
            self.writeFile('README.md', '# Test Repository')
            self.git(["add", "."])
            self.commitAsBot('Initial commit')
            self.initial = self.git(["rev-parse", "HEAD"])

            self.git(["remote", "add", "origin", "file://" + self.origin])

            logOutput = self.log()
            expected = 'Pantheon Automation <bot@getpantheon.com> Initial commit'
            print('EXPECTED:', repr(expected))
            print('ACTUAL:', repr(logOutput.decode().strip()))
            assert expected == logOutput.decode().strip()

            # CONTROL PART II:
            #
            # Create a 'default' branch with a fake .circleci directory

            self.createBranch('default')
            os.mkdir(self.repo + '/.circleci')
            self.writeFile('.circleci/config.yml', '# Fake CircleCI configuration file')
            os.mkdir(self.repo + '/.github')
            os.mkdir(self.repo + '/.github/workflows')
            self.writeFile('.github/workflows/update_tag1_d7es.yml', '# Fake GHA Workflow file')
            self.git(["add", '.circleci/config.yml'])
            self.git(["add", '.github/workflows/update_tag1_d7es.yml'])
            self.commitAsBot("Add CircleCI configuration")

            logOutput = self.log()
            assert """Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # TEST SIMPLE AUTOMERGE AS BOT:
            #
            # Add a commit to 'default' using bot, then run automerge script.
            # Assert that the new commit exists on the master branch.

            self.addToDefault('CHANGELOG.md', 'This is a fake release')
            self.commitAsBot('Add a test commit')
            logOutput = self.log()

            # Assert that our test commit is now at the HEAD of the default branch.
            assert """Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # Run our test!
            automergeOutput = self.runAutomerge()

            self.switchBranch('default')
            logOutput = self.log()

            # Assert that the 'default' branch now has the CircleCI commit
            # as the HEAD commit, and the test commit we added earlier is
            # now in the second position after it.
            assert """Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            self.switchBranch('master')
            logOutput = self.log()

            # Assert that the commit we added to 'default' now exists on
            # the 'master' branch, but the CircleCI commit does not.
            assert """Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # TEST AUTOMERGE AS USER
            #
            # Add a commit to 'default' using a user account, then run automerge script.
            # Assert that the new commit does not exist on the master branch.

            self.addToDefault('CUSTOMIZATIONS.md', 'Fake platform customization')
            self.commitAsUser('Add a commit as a user')
            logOutput = self.log()

            print("Log output in question:")
            print(logOutput)

            # Assert that our test commit is now at the HEAD of the default branch.
            assert """J. Doe <doe@example.com> Add a commit as a user
Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # Run our test!
            automergeOutput = self.runAutomerge()

            self.switchBranch('default')
            logOutput = self.log()

            print("Log of default branch after script: ")
            print(logOutput)
            # Assert that the 'default' branch has not changed.
            assert """J. Doe <doe@example.com> Add a commit as a user
Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            self.switchBranch('master')
            logOutput = self.log()

            # Assert that the 'master' branch has not changed.
            assert """Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # TEST AUTOMERGE AS BOT AFTER A COMMIT BY A USER:
            #
            # Add a commit to 'default' using bot on top of an unmerged
            # commit from a user, then run automerge script.
            # Assert that both of these commits exist on the master branch.

            self.addToDefault('CHANGELOG.md', 'Yet another fake release', 'a')
            self.commitAsBot('Simulate a release')
            logOutput = self.log()

            # Assert that our test commit is now at the HEAD of the default branch.
            assert """Pantheon Automation <bot@getpantheon.com> Simulate a release
J. Doe <doe@example.com> Add a commit as a user
Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            # Run our test!
            automergeOutput = self.runAutomerge()

            self.switchBranch('default')
            logOutput = self.log()

            # Assert that the 'default' branch now has the CircleCI commit
            # as the HEAD commit, and both the bot and the previous user
            # commits now appear after it.
            assert """Pantheon Automation <bot@getpantheon.com> Add CircleCI configuration
Pantheon Automation <bot@getpantheon.com> Simulate a release
J. Doe <doe@example.com> Add a commit as a user
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

            self.switchBranch('master')
            logOutput = self.log()

            # Assert that all of our test commits have made it to the 'master'
            # branch, but the CircleCI commit does not.
            assert """Pantheon Automation <bot@getpantheon.com> Simulate a release
J. Doe <doe@example.com> Add a commit as a user
Pantheon Automation <bot@getpantheon.com> Add a test commit
Pantheon Automation <bot@getpantheon.com> Initial commit""" == logOutput.decode().strip()

        finally:
            shutil.rmtree(self.tmpdir)
            print("Done!")

if __name__ == "__main__":
    unittest.main()
