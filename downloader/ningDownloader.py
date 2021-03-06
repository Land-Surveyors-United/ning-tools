#!/usr/bin/env python
"""Ning network data downloader

Downloads data from a Ning network using the Ning REST API


"""

__author__ = "Turadg Aleahmad (turadg@cmu.edu)"
__version__ = "$Revision: 0.4.2 $"
__date__ = "$Date: 2008/11/18 7:57:19 $"
__copyright__ = "Copyright (c) 2008 Turadg Aleahmad"
__license__ = "GPL"

from xml.dom import minidom
#from lxml import etree
from datetime import *
import random
import sys, shutil
from optparse import *
import csv
import urllib, urllib2, base64
import os
import re
import time

class NingDownloader:
	"""dumps data from Ning networks"""

	def __init__(self, options):
	   self.options = options
	   return

	def run(self):
		# endpoint = self.options.endpoint
		# methodMap = dict(profile=DataDumper.downloadProfiles,
		# 				 rollup=DataDumper.downloadRollup,
		# 				 content=DataDumper.downloadContent)
		# handler = methodMap.get(endpoint)
		# handler(self)
		self.downloadAll()

	def downloadRange (self, start, end):
		start = str(start)
		end = str(end)
		
		base = self.baseUrl()
		url = "%s?order=published@D&from=%s&to=%s" % (base, start, end)
		
		user = self.options.username
		password = self.options.password
		
		if (password):
			if (self.options.verbose): print "authenticating with user: %s and password: %s\n" % (user, password)
			base64auth = base64.encodestring('%s:%s' % (user, password)).strip()
			headers = {'Authorization': "Basic %s" % base64auth }
			request = urllib2.Request(url, headers=headers)
		else:
			url += "&xn_auth=no"
			request = urllib2.Request(url)
		
		if (self.options.verbose): print "requesting %s" % url
		
		try:
			response = urllib2.urlopen(request)
		except urllib2.HTTPError, err:
			if 200 <= err.code < 300:
				response = err
			else:
				raise err
		
		network = self.options.network
		endpoint = self.options.endpoint
		fn = self.outputFilename(start,end)
		f = open(fn, 'w')
		shutil.copyfileobj(response.fp, f)
		f.close()
		if (self.options.verbose): print "wrote: %s\n  to file %s\n" % (url, fn)
		return fn

	def fdate(datetime):
		"""format datetime for Ning API"""
		return datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

	@staticmethod
	def dayContentSelector(day):
		start = day
		end = datetime.fromordinal(day.toordinal()+1)
		return "createdDate > " + start.isoformat() + "&createdDate < " + end.isoformat()

	def dayContent(self, day, type=None):
		"""load counts of each content type and output them"""
		self.table = {}
		url = "http://%s.ning.com/xn/atom/1.0/content(" % self.options.networks
		if (type != None): url += "type='" + type + "'&"
		url += urllib.quote(self.dayContentSelector(day)) + ")"
		self.feed = self._load(url, day.isoformat() + " " + type)

	def downloadDays(self, startN, endN, type=None):
		for i in range(startN, endN + 1):
			day = datetime.fromordinal(i)
			print "Getting day " + day.isoformat() + " (" + str(i-startN) + "/" + str(endN-startN) + ")"
			self.dayContent(day, type)

	def downloadProfiles(self):
		raise NameError, 'downloadProfiles not yet implemented'

	def downloadAll(self):
		i = 0 # count of hundreds
		while True:
			startN = i * 100
			endN = (i + 1) * 100  # i.e. startN + 100
			filename = self.downloadRange(startN, endN)
			# this is the same for all but empty results, so we can know the stop condition at the beginning
			xnSize = self.xnSize(filename) 
			if xnSize < 100 or endN > xnSize:
				if (self.options.verbose): print "Terminating with xnSize %i" % xnSize
				break
			i += 1 # otherwise increment for next iteration


	def baseUrl(self):
		""" to this will be added e.g. from=0&to=100 """
		endpoint = self.options.endpoint
		if endpoint == 'rollup': endpoint = 'content/rollup'
		url = "https://%s.ning.com/xn/atom/1.0/%s(%s)" % (self.options.network, endpoint, self.options.selector)
		if (self.options.verbose): print "base url: %s" % url
		return url

	def outputFilename(self, startRange, endRange):
		return "%s-%s-%s-%s-%s.xml" % (self.options.network, self.options.endpoint, self.options.selector, startRange, endRange)

	@staticmethod
	def xnSize(filename):
		reg = re.compile('<xn:size>(.*)</xn:size>')
		f = open(filename, 'r')

		for line in f:
			m = reg.search(line)
			if m:
				size = int(m.groups()[0])
				break
		f.close()
		return size	


	def output(self, method):
		"""output generated text"""
		if (method=='xml'):
			return self.feed.toxml()
		elif (method=='csv'):
			print self.table.keys()
			writer = csv.DictWriter(open("some.csv", "wb"), ['key', 'count'])
			writer.writerow(dict(key='key', count='count'))
			for k, v in self.table.iteritems():
				i = dict(key=k, count=v)
				print i
				writer.writerow(i)


def main(argv):
	cl2start = datetime(2007,03,23)
	fmt = "%Y-%m-%d"
	parser = OptionParser()
	parser.add_option("-n", "--network", dest="network", help="Ning network to dump (NAME.ning.com)", default="educationresearch")
	parser.add_option("-u", "--username", dest="username", help="Ning network owner username", default="turadg", metavar="USER")
	parser.add_option("-p", "--password", dest="password", help="Ning network owner password", metavar="PASS")
	parser.add_option("-e", "--endpoint", dest="endpoint", help="Ning REST endpoint", choices=["content", "rollup", "profile"], default="rollup")
	parser.add_option("-s", "--selector", dest="selector", help="selector for endpoint", default="field='type'")
	parser.add_option("-d", "--date", dest="startDate", help="date to start querying over in ISO 8601 format", default=cl2start.strftime(fmt))
	parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="verbose")
	(options, args) = parser.parse_args()

	try:
		options.oDate = datetime.strptime(options.startDate, fmt)
	except:
		raise OptionValueError("date option invalid %s" % options.startDate)

	d = NingDownloader(options)
	if (options.verbose): print options

	d.run()


if __name__ == "__main__":
	main(sys.argv[1:])
