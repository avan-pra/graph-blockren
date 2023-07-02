from typing import List

from neo4j import GraphDatabase

from tempfile import mkstemp
from os import fdopen

from utils import *
from utils.arg_wrapper import argparse_wrapper

import pickle
import re

def fetch(args):
	""" Responsible for the fetch function
	- Connect to rpc endpoint
	- Verify the user inputed range
	- Fetch block in a list
	- Pickle them and write them to a file
	"""

	w3 = init_web3(args.chain)
	storage = ImportStorage()
	storage.rpc_url = args.chain
	blocklist = []

	for group in args.blocks.split(','):
		if re.match(r'[0-9]+-[0-9]+', group):
			start, end = [int(i) for i in group.split('-')]
			if not start <= end:
				raise BaseException(f"block {start} is > to {end}")
			blocklist += range(start, end + 1)
		else:
			blocklist.append(int(group))

	print(f"Fetching a total of {len(blocklist)} block")
	for blocknbr in blocklist:
		block = w3.eth.get_block(blocknbr, full_transactions=True)
		storage.blocklist.append(block)

	fd, filename = mkstemp()
	with fdopen(fd, 'wb') as blockfile:
		print(f"Writing {len(storage.blocklist)} blocks to {filename}")
		pickle.dump(storage, blockfile)

	print("Done")

def importf(args):
	""" Responsible for the import functionality
	- Initiate a connection to the neo4j db
	- Verify the connection
	- Read the save file and pickle.loads a list of block
	- Iterate over every transaction in every block and call the importer
	"""
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:

			# if not driver.verify_connectivity():
			# 	raise BaseException(driver)
			# if not driver.verify_authentication():
			# 	raise BaseException(driver)
			print(f"Connected to {args.database}")

			imported_file = open(args.file, 'rb')
			storage: ImportStorage = pickle.loads(imported_file.read())
			print(f"Importing {sum([len(block['transactions']) for block in storage.blocklist])} transactions")
			for block in storage.blocklist:
				session.execute_write(import_block, block)
				for transaction in block['transactions']:
					session.execute_write(import_transaction, transaction)

			if (args.contract):
				w3 = init_web3(storage.rpc_url)
				transactions = session.execute_read(submit, "MATCH ({addr: 'None'})-[r]-() return r")
				print(f"Found a total of {len(transactions)} contract")
				for transaction in transactions:
					receipt = w3.eth.get_transaction_receipt(transaction['r']['hash'])
					session.execute_write(create_contract_relation, receipt, transaction['r'])

				print("Removing 'Contract Creation' dummy node")
				session.execute_write(submit, "MATCH (n:`Contract Creation`) DETACH DELETE n")	

	print("Done")

def deletedb(args):
	""" Simply delete all nodes """
	with GraphDatabase.driver(args.database, auth=(args.user, args.password)) as driver:
		with driver.session() as session:
			session.execute_write(submit, "match (n) detach delete n")
	print("Done")

def dev(args):
	from custom.heroctf import heroctf
	heroctf(args)

def main():
	args = argparse_wrapper()
	action_array = {
		"fetch": fetch,
		"import": importf,
		"delete": deletedb,
		"dev": dev
	}
	action_array[args.action](args)

if __name__ == "__main__":
	main()
