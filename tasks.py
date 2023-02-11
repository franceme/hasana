#!/usr/bin/env python3
import os,sys
from invoke import task


@task
def gitr(c):
	for x in [
		'git config --global user.email "EMAIL"',
		'git config --global user.name "UserName (dev@lite)"'
	]:
		print(x);os.system(x)

@task
def cleanenv(c):
	for x in [
		'CachedExtensions/',
		'CachedExtensionVSIXs/',
		'User/',
		'Machine/',
		'extensions/',
		'logs/',
		'coder.json',
		'machineid',
	]:
		x = "yes|rm -r " + str(x)
		print(x);os.system(x)

@task
def execute(c):
	print("Executing")
