#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010 Julius Plenz <julius@plenz.com>
# Copyright (C) 2010 Valentin Haenel <valentin.haenel@gmx.de>
# Licensed under GPL v3 or later

import os
import tempfile as tf
import shutil as sh
import unittest as ut
import git_big_picture as gbp
import git_big_picture.git_tools as gt

class TestGitTools(ut.TestCase):

	def setUp(self):
		self.testing_dir = tf.mkdtemp(prefix='gbp-testing-', dir="/tmp")
		gbp.git_tools.git_env = {'GIT_DIR' : "%s/.git" % self.testing_dir }
		gt.get_command_output(['git', 'init', self.testing_dir])

	def tearDown(self):
		sh.rmtree(self.testing_dir)

	def test_get_parent_map(self):
		def dispatch(command_string):
			return gt.get_command_output(command_string.split(' '))

		def get_head_sha():
			return dispatch('git rev-parse HEAD').rstrip()

		oldpwd = os.getcwd()
		os.chdir(self.testing_dir)

		dispatch('/usr/bin/git init')
		dispatch('git config user.name git-big-picture')
		dispatch('git config user.email git-big-picture@example.org')

		dispatch('git commit --allow-empty -m 1')
		sha_1 = get_head_sha()
		dispatch('git commit --allow-empty -m 2')
		sha_2 = get_head_sha()
		dispatch('git checkout -b other HEAD^')
		dispatch('git commit --allow-empty -m 3')
		sha_3 = get_head_sha()
		dispatch('git merge --no-ff master')
		sha_4 = get_head_sha()

		expected_parents = {
			sha_1:set(),
			sha_2:set((sha_1,)),
			sha_3:set((sha_1,)),
			sha_4:set((sha_2, sha_3)),
		}

		actual_parents = gt.get_parent_map()

		self.assertEqual(actual_parents, expected_parents)

		os.chdir(oldpwd)

# vim: set noexpandtab:
