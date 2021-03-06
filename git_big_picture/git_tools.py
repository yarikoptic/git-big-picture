# -*- coding: utf-8 -*-
# Copyright (C) 2010 Sebastian Pipping <sebastian@pipping.org>
# Copyright (C) 2010 Julius Plenz <julius@plenz.com>
# Copyright (C) 2010 Valentin Haenel <valentin.haenel@gmx.de>
# Licensed under GPL v3 or later

import subprocess
import re

sha1_pattern = re.compile('[0-9a-fA-F]{40}')
git_env = None

def get_command_output(command_list):
	""" Execute arbitrary commands.

	Parameters
	----------
	command_list : list of strings
		the command and its arguments

	Returns
	-------
	output : string
		the raw output of the command executed
	"""

	p = subprocess.Popen(command_list, stdout=subprocess.PIPE,
			stderr=subprocess.PIPE, env=git_env)
	load = p.stdout.read()
	p.wait()
	if p.returncode:
		err = p.stderr.read()
		err = '\n'.join(('> ' + e) for e in err.split('\n'))
		raise Exception('Stderr:\n%s\nReturn code %d from command "%s"' \
			% (err, p.returncode, ' '.join(command_list)))
	return load

def get_mappings():
	""" Get mappings for all refs.

	This is implemented using a single call to 'git for-each-ref'. Note that it
	can handle non commit tags too and retruns these

	Returns
	-------
	(lbranches, rbranches, abranches), (tags, ctags, nctags)

	lbranches : dict mapping strings to sets of strings
		mapping of commit sha1s to local branch names
	rbranches : dict mapping strings to sets of strings
		mapping of commit sha1s to remote branch names
	abranches : dict mapping strings to sets of strings
		mapping of commit sha1s to all branch names
	tags : dict mapping strings to sets of strings
		mapping of object sha1s to tag names
	ctags : dict mapping sha1s to sets of strings
		mapping of commits sha1s to tag names
	nctags : dict mapping sha1s to sets of strings
		mapping of non-commit sha1s to sets of strings
	"""

	output = get_command_output(['git', 'for-each-ref',
		"--format=['%(objectname)', '%(*objectname)',  '%(objecttype)', '%(refname)']"]).splitlines()
	lbranch_prefix = 'refs/heads/'
	rbranch_prefix = 'refs/remotes/'
	tag_prefix = 'refs/tags/'
	lbranches = dict()
	rbranches = dict()
	abranches = dict()
	tags = dict()
	ctags = dict()
	nctags = dict()
	def add_to_dict(dic, sha1, name):
		if sha1 not in dic:
			dic[sha1] = set()
		dic[sha1].add(name)

	for ref_info in output:
		sha1, tag_sha1, ref_type, name = eval(ref_info)
		if ref_type not in ['commit', 'tag']:
			continue
		elif name.startswith(lbranch_prefix):
			add_to_dict(lbranches, sha1, name.replace(lbranch_prefix, ''))
			add_to_dict(abranches, sha1, name.replace(lbranch_prefix, ''))
		elif name.startswith(rbranch_prefix):
			add_to_dict(rbranches, sha1, name.replace(rbranch_prefix, ''))
			add_to_dict(abranches, sha1, name.replace(rbranch_prefix, ''))
		elif name.startswith(tag_prefix):
			# recusively dereference until we find a non-tag object
			sha1 = get_command_output(['git', 'rev-parse',
				name+'^{}']).splitlines()[0]
			# determine object type and to respective dict
			obj_type = get_command_output(['git', 'cat-file', '-t',
				sha1]).splitlines()[0]
			if obj_type in ['blob', 'tree']:
				add_to_dict(nctags, sha1, name.replace(tag_prefix, ''))
			else:
				add_to_dict(ctags, sha1, name.replace(tag_prefix, ''))
			add_to_dict(tags, sha1, name.replace(tag_prefix, ''))

	return (lbranches, rbranches, abranches), (tags, ctags, nctags)

def get_parent_map():
	""" Get a mapping of children to parents.

	Returns
	-------
	parents : dict mapping strings to sets of strings
		mapping of children sha1s to parents sha1
	"""

	parents = {}
	p = subprocess.Popen(['git', 'rev-list', '--all', '--parents'], stdout=subprocess.PIPE, env=git_env)
	output = p.communicate()[0]
	for line in output.split('\n'):
		sha_ones = [e.group(0) for e in re.finditer(sha1_pattern, line)]
		count = len(sha_ones)
		if count > 1:
			parents[sha_ones[0]] = set(sha_ones[1:])
		elif count == 1:
			parents[sha_ones[0]] = set()
	return parents

