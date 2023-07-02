import argparse

def argparse_wrapper():
	parser = argparse.ArgumentParser(
		description='A tool to vizualize eth blockchain transaction using a graph database'
	)
	subparser = parser.add_subparsers(dest='action', required=True)
	fetch = subparser.add_parser('fetch', help='fetch blockchain data')
	fetch.add_argument('-c', '--chain', required=True, help='A chain URI (rpc url)')
	fetch.add_argument('-b', '--blocks', required=True, help='Blocks to fetch (inclusive if range) example: 3529374-3529377,25,26,55-57 will fetch blocks 3529374, 3529375, 3529376, 3529377, 25, 26, 55, 56 and 57')
	db = subparser.add_parser('import', help='import collected data to database')
	db.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	db.add_argument('-f', '--file', help='file to parse', required=True)
	db.add_argument('--user', help='username for neo4j database', default='neo4j')
	db.add_argument('--password', help='password for neo4j database', default='password')
	db.add_argument('-c', '--contract', help='connect to the chain again and fetch the contract address for every created contract inside the database', action='store_true')
	deletedb = subparser.add_parser('delete', help='delete all nodes in your neo4j database')
	deletedb.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	deletedb.add_argument('--user', help='username for neo4j database', default='neo4j')
	deletedb.add_argument('--password', help='password for neo4j database', default='password')
	dev = subparser.add_parser('dev', help='want to run your own custom code ?')
	dev.add_argument('-d', '--database', help='neo4j database url', default='bolt://localhost:7687')
	dev.add_argument('--user', help='username for neo4j database', default='neo4j')
	dev.add_argument('--password', help='password for neo4j database', default='password')
	dev.add_argument('-c', '--chain', help='A chain URI (rpc url)', default='https://rpc.sepolia.org/')
	return parser.parse_args()